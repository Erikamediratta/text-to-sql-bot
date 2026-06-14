from sqlalchemy import inspect, text
from google import genai
import os
from dotenv import load_dotenv
load_dotenv()

from db import get_engine, dialect_name
from guardrails import is_safe_sql

import streamlit as st


client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash-lite" 


# 1. Read database schema
def get_schema():
    engine = get_engine()
    inspector = inspect(engine)
#inspects reads db structure (tables,columns)

    schema_lines = []

    for table in inspector.get_table_names():
        cols = inspector.get_columns(table)
        col_names = [c["name"] for c in cols]
        schema_lines.append(f"{table}({', '.join(col_names)})")
        #example-customers(id, name, city)

    return "\n".join(schema_lines)
#final schema string sent to GPT


# 2. Convert question → SQL
def generate_sql(question: str):
    schema = get_schema()
    dialect = dialect_name()

    prompt = f"""
You are a senior {dialect} SQL expert.

You must follow STRICT rules:

RULES:
1. Use ONLY required tables (do NOT add unnecessary JOINs)
2. For COUNT questions → use COUNT(*) directly
3. Do NOT duplicate rows using joins unless needed
4. Use exact column filters from schema
5. Return ONLY SQL (no explanation, no markdown)

SCHEMA:
{schema}

EXAMPLES:

Q: How many customers are there?
SQL: SELECT COUNT(*) FROM customers

Q: How many customers are from Delhi?
SQL: SELECT COUNT(*) FROM customers WHERE city = 'Delhi'

Q: How many orders have status completed?
SQL: SELECT COUNT(*) FROM orders WHERE status = 'completed'

Q: How many products are in electronics?
SQL: SELECT COUNT(*) FROM products WHERE category = 'electronics'

NOW ANSWER:

Question: {question}
SQL:
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text.strip()
# 3. Run SQL on database
def run_query(sql: str):
    engine = get_engine()
   

    with engine.connect() as conn:
        result = conn.execute(text(sql))
        #runs sql query
        cols = result.keys()
        rows = result.fetchall()

#         cols → column names
# rows → actual data

    return list(cols), rows
    #returns structured results

# 4. Convert result → English
def explain(question, sql, cols, rows):
    prompt = f"""
Question: {question}
SQL: {sql}
Columns: {cols}
Rows: {rows}

Explain this result in simple English in 1–2 lines.
"""
    response = client.models.generate_content(
    model=MODEL,
    contents=prompt
)

    return response.text.strip()
   

#example input Rows: [(5,)]
#GPT converts it into: 
#There are 5 customers 

# 5. MAIN PIPELINE
def ask(question: str,history=""):
    try:
        # Step 1: generate SQL from GPT
        raw_sql = generate_sql(question)

        # Step 2: guardrail check (IMPORTANT SECURITY STEP)
        if not is_safe_sql(raw_sql):
            return {
                "ok": False,
                "sql": raw_sql,
                "answer": "Blocked by guardrails (unsafe SQL)"
            }

        sql = raw_sql

        # Step 3: execute SQL
        cols, rows = run_query(sql)

        # Step 4: explain result using GPT
        answer = explain(question, sql, cols, rows)

        return {
            "ok": True,
            "sql": sql,
            "columns": cols,
            "rows": rows,
            "answer": answer
        }

    except Exception as e:
        return {
            "ok": False,
            "sql": None,
            "answer": f"Execution error: {e}"
        }


# 6. Manual test
if __name__ == "__main__":
    print(ask("How many customers are there?"))