# Text-to-SQL Chatbot

Ask questions about a database in plain English. An AI model (Google Gemini)
writes the SQL for you, the query runs against a real database, and the result
comes back as a plain-English answer — so anyone can "query a database" without
knowing SQL.

```
You: How many customers are from Delhi?

  SQL:    SELECT COUNT(*) FROM customers WHERE city = 'Delhi'
  Answer: There are 3 customers from Delhi.
```

You never wrote SQL. The system wrote it, ran it, and explained the result.

---

## What makes this different from a normal chatbot

A normal chatbot just returns text. This project makes the AI produce **runnable
SQL**, then **executes it** against a live database. Because running AI-generated
SQL is risky (a bad query could damage data), the project includes a **safety
layer** that blocks dangerous queries before they ever run. That extra
"generate → check → execute → explain" loop is what turns a chatbot into a tool
that actually *does* something.

---

## How it works (the pipeline)

Every question flows through the same five steps:

```
   your question
        │
   (1) read the database schema        →  so the AI knows the tables & columns
        │
   (2) AI writes a SQL query           →  English turned into SQL
        │
   (3) guardrails check the SQL        →  SAFETY: block anything dangerous
        │
   (4) run the SQL on the database     →  get the actual data
        │
   (5) AI explains the result          →  data turned back into English
        │
   plain-English answer
```

---

## Project files

| File | Job |
|------|-----|
| `db.py` | Connects to the database (works with SQLite or MySQL). |
| `seed_db.py` | Creates the tables and fills them with sample data. Run once. |
| `guardrails.py` | The safety check. Decides if a SQL query is safe to run. |
| `engine.py` | The brain. Question → SQL → run → English answer. |
| `app_cli.py` | The chatbot you talk to in the terminal (with memory). |
| `evaluate.py` | Tests how accurate the bot is, with a score. |
| `.env` | Your secret keys (Gemini API key). Never share this. |
| `requirements.txt` | The Python libraries to install. |

**Read the files in this order to understand them:**
`db.py` → `seed_db.py` → `guardrails.py` → `engine.py` → `app_cli.py` → `evaluate.py`

---

## Setup

### 1. Install the libraries

```bash
pip install -r requirements.txt
```

`requirements.txt` contains:

```
google-genai        # the Google Gemini SDK (this is what `from google import genai` needs)
sqlalchemy          # talks to the database (SQLite or MySQL) with one set of code
python-dotenv       # loads your API key from the .env file
pymysql             # MySQL driver (only needed if you use MySQL instead of SQLite)
```

### 2. Add your API key

Create a file named `.env` in the project folder:

```
GEMINI_API_KEY=your_key_here
```

Optionally, to use MySQL instead of the default SQLite, also add:

```
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/yourdbname
```

If you leave `DATABASE_URL` out, the project uses a local SQLite file
(`company.db`) automatically — zero setup needed.

### 3. Create the database

```bash
python seed_db.py
```

You should see `Strong database seeded!`. This creates four tables and fills them
with sample customers, products, and orders.

### 4. Start chatting

```bash
python app_cli.py
```

Type questions. Type `/reset` to clear memory, or `exit` to quit.

---

## The database (what you can ask about)

Four tables, connected to each other:

- **customers** — `id, name, city, segment` (who buys)
- **products** — `id, name, category, price` (what's for sale)
- **orders** — `id, customer_id, status, order_date` (a purchase by a customer)
- **order_items** — `id, order_id, product_id, quantity` (which products were in each order)

They're split across tables on purpose. To answer something like "total revenue,"
the AI has to **JOIN** these tables back together — connecting an order to its
items, each item to its product's price, and so on. Writing those JOINs correctly
is the impressive part the AI does for you.

---

## Understanding each file

### `db.py` — the database connection

Its only job is to hand the rest of the project a connection, without anyone
caring whether it's SQLite or MySQL.

- It reads `DATABASE_URL` from your `.env`. If it's not set, it defaults to a
  local SQLite file. That's why the project runs with zero setup but can switch
  to MySQL by changing one line.
- `get_engine()` returns the "connection" object (SQLAlchemy calls it an
  *engine*) that other files use to talk to the database.
- `dialect_name()` just reports whether you're on `sqlite` or `mysql`, so the AI
  prompt can say "you are a sqlite/mysql expert" and match the right syntax.

**Why SQLAlchemy?** It's a translator that lets the *same code* work on SQLite
and MySQL. You write once; it handles each database's differences.

### `seed_db.py` — building the database

This file defines the four tables and fills them with data. You run it once.

- The tables are defined using SQLAlchemy `Table(...)` objects instead of raw
  `CREATE TABLE` SQL. This lets SQLAlchemy generate the correct table-creation
  code for whichever database you're using.
- `ForeignKey("customers.id")` records a relationship — for example, that
  `orders.customer_id` points at a customer. This is the link a JOIN follows.
- `metadata.drop_all(engine)` then `metadata.create_all(engine)` resets the
  tables to a clean state every run, so the data is always predictable.
- The rows are inserted inside `with engine.begin() as conn:` — a *transaction*,
  which means all the inserts are saved together safely.

### `guardrails.py` — the safety check (the most important file)

This is what makes running AI-generated SQL safe. The AI is **not trusted** —
it could make a mistake, or a user could try to trick it into deleting data. So
before any query runs, this file inspects it.

```python
FORBIDDEN = ["drop", "delete", "update", "insert"]

def is_safe_sql(sql):
    sql = sql.lower()
    for word in FORBIDDEN:
        if word in sql:
            return False     # dangerous word found → block it
    return True              # clean → allow it
```

How it works in plain English: it lowercases the query, then checks whether any
"dangerous" word (`drop`, `delete`, `update`, `insert` — the words that change or
destroy data) appears in it. If one does, the query is blocked and never runs.
A normal `SELECT` (which only *reads* data) contains none of these, so it passes.

**Without this file**, the AI could generate `DROP TABLE customers` and your
database would be destroyed. That's why `engine.py` calls `is_safe_sql()` before
executing anything.

> **Known limitation (good to know for interviews):** this is a simple
> *blocklist* that checks for substrings. It's effective against the obvious
> dangers, but it isn't bulletproof — for example, a harmless column named
> `order_updated` contains the substring `update` and would be wrongly blocked. A
> more robust version would (a) *allow only* queries that start with `SELECT`
> (an allowlist is safer than a blocklist), (b) match whole words instead of
> substrings, and (c) connect with a read-only database user so writes are
> impossible even if a query slips through. Mentioning this upgrade path shows
> you understand the trade-off.

### `engine.py` — the brain

This is where the whole pipeline lives. It uses Gemini for the two AI steps
(writing SQL and explaining the result).

It sets up the Gemini client once:

```python
from google import genai
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"
```

Then five functions, matching the pipeline:

- **`get_schema()`** — reads the live database's tables and columns and returns a
  string like `customers(id, name, city, segment)`. This is what tells the AI
  what it's allowed to query. (This is the equivalent of "retrieval" in a RAG
  chatbot: gather the context the model needs before asking it to produce
  something.)

- **`generate_sql(question)`** — builds a prompt containing the rules, the schema,
  a few example question→SQL pairs, and your question, then asks Gemini to write
  the SQL. The example pairs ("few-shot examples") teach the model the pattern
  and sharply improve accuracy.

- **`run_query(sql)`** — opens a connection and runs the SQL, returning the column
  names and the result rows.

- **`explain(question, sql, cols, rows)`** — hands Gemini the raw result (e.g.
  `rows = [(3,)]`) and asks it to phrase a natural sentence: "There are 3
  customers from Delhi."

- **`ask(question, history)`** — the orchestrator that ties it together:
  generate SQL → **check with `is_safe_sql`** → run → explain. If the safety
  check fails, it returns "Blocked by guardrails" and never touches the database.
  It returns a dictionary with both the `sql` and the `answer`, so the chatbot
  can show both.

### `app_cli.py` — the chatbot interface

A loop that reads your question, calls `ask()`, and prints the SQL and the answer.

Its special feature is **memory**. It keeps the last few question→SQL pairs and
passes them back into `ask()` as context:

```python
MAX_MEMORY_TURNS = 3
ctx = format_history(history[-MAX_MEMORY_TURNS:])
result = ask(question, history=ctx)
```

This lets follow-up questions work. After "How many customers are from Delhi?"
you can ask "What about Mumbai?" and the model understands you mean *customers
from Mumbai*, because it can see the previous turn. It only keeps the last 3
turns, because too much history bloats the prompt. `/reset` clears the memory.

It also prints the SQL alongside every answer — that transparency builds trust
and makes debugging easy (if an answer looks wrong, you can see the exact query
that produced it).

### `evaluate.py` — measuring accuracy

This proves the bot works, with a number — which is exactly the kind of thing
that makes the project stand out.

```python
TEST_SET = [
    ("How many customers are there?", 7),
    ("How many customers are from Delhi?", 3),
    ("How many orders have status completed?", 6),
    ("How many products are in electronics?", 3),
]
```

Each pair is a question and the answer it *should* produce (these values were
verified against the actual seeded data). The script runs each question, gets
the result, and compares it to the expected value, then prints a final score
like `4 / 4`.

**Why a "fake" SQL generator?** This file uses a small hardcoded
question → SQL mapping instead of calling Gemini:

```python
def generate_sql(question):
    mapping = { "How many customers are there?": "SELECT COUNT(*) FROM customers", ... }
    return mapping.get(question, "")
```

That's deliberate and smart — it lets you test the *pipeline* (the database, the
guardrails, the result comparison) **without spending API calls or hitting rate
limits**. The expected values come from the real database, so the test still
proves the data and queries are correct.

> **Note:** because the expected numbers must match your seed data, if you ever
> change the data in `seed_db.py`, update the expected values here too. (A
> mismatch shows up as a `FAIL` even when the SQL is correct — the test is
> comparing against the wrong number, not finding a bug.)

---

## Example run

```
Text-to-SQL Chatbot (CLI)
Type 'exit' to quit, '/reset' to clear memory

Ask a question: How many customers are from Delhi?

SQL: SELECT COUNT(*) FROM customers WHERE city = 'Delhi'
Answer: There are 3 customers from Delhi.

Ask a question: What is the total revenue from completed orders?

SQL: SELECT SUM(p.price * oi.quantity)
     FROM orders o
     JOIN order_items oi ON oi.order_id = o.id
     JOIN products p ON p.id = oi.product_id
     WHERE o.status = 'completed'
Answer: The total revenue from completed orders is ...
```

---

## Tech stack

- **Python**
- **Google Gemini** (`gemini-2.5-flash`) — writes the SQL and explains results
- **SQLAlchemy** — database access that works on SQLite and MySQL
- **SQLite / MySQL** — the database
- **python-dotenv** — loads the API key

---

## Key ideas this project demonstrates

- **Grounding** — the AI doesn't answer from memory; it runs a real query and
  answers from the actual data, which prevents made-up answers.
- **Structured output** — the AI produces precise, runnable SQL, not just text.
- **Safety first** — AI output is never executed without a guardrail check.
- **Few-shot prompting** — example queries in the prompt improve accuracy.
- **Evaluation** — accuracy is measured with a test set, not just assumed.

---

## Possible next steps

- Strengthen `guardrails.py` (allow only `SELECT`, whole-word matching, read-only
  database user).
- Add a web UI (e.g. Streamlit) so it's clickable.
- Expand the test set in `evaluate.py` with harder JOIN questions.
- Add row limits and query timeouts for safety on larger databases.
