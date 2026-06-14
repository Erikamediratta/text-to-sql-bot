import streamlit as st
import pandas as pd
from sqlalchemy import inspect, text

from db import get_engine
from engine import ask

st.set_page_config(page_title="Text-to-SQL Bot", page_icon="🧠", layout="wide")


# ---------------------------------------------------------------------------
# Helpers: read the live schema + a small data preview so the UI is self-explanatory
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_schema():
    insp = inspect(get_engine())
    return {t: [c["name"] for c in insp.get_columns(t)] for t in insp.get_table_names()}


@st.cache_data(show_spinner=False)
def preview(table, limit=5):
    with get_engine().connect() as conn:
        res = conn.execute(text(f"SELECT * FROM {table} LIMIT {limit}"))
        return pd.DataFrame(res.fetchall(), columns=list(res.keys()))


EXAMPLES = [
    "How many customers are there?",
    "How many customers are from Delhi?",
    "How many orders have status completed?",
    "How many products are in electronics?",
    "What is the total revenue from completed orders?",
    "List all customers in the business segment",
]


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "question" not in st.session_state:
    st.session_state.question = ""
if "run" not in st.session_state:
    st.session_state.run = False
if "history" not in st.session_state:
    st.session_state.history = []


def use_example(q):
    """Fill the box with an example and trigger a run on the next rerun."""
    st.session_state.question = q
    st.session_state.run = True


# ---------------------------------------------------------------------------
# Sidebar — the database explorer (this is what was missing!)
# ---------------------------------------------------------------------------
schema = load_schema()
with st.sidebar:
    st.header("📚 The Database")
    st.caption(
        "Your plain-English questions are turned into SQL, run against these "
        "tables, and explained. Expand a table to see its columns and sample rows."
    )
    for table, cols in schema.items():
        with st.expander(f"🗂️  {table}  ·  {len(cols)} columns"):
            st.markdown("**Columns:** " + ", ".join(cols))
            try:
                st.dataframe(preview(table), use_container_width=True, hide_index=True)
            except Exception:
                st.write("_(preview unavailable)_")


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------
st.title("🧠 Text-to-SQL Chatbot")
st.write(
    "Ask a question about the database in plain English. The AI writes the SQL, "
    "runs it on a live database, and explains the result — so you can query data "
    "**without knowing SQL**. Not sure what to ask? The tables are in the sidebar 👈, "
    "or tap an example below."
)

st.markdown("**Try an example:**")
cols = st.columns(3)
for i, ex in enumerate(EXAMPLES):
    cols[i % 3].button(
        ex, key=f"ex_{i}", use_container_width=True, on_click=use_example, args=(ex,)
    )

st.text_input("Or type your own question:", key="question")
ask_clicked = st.button("Ask", type="primary")

# Run when the user clicks Ask, or when an example was tapped
if ask_clicked or st.session_state.run:
    st.session_state.run = False
    q = st.session_state.question.strip()

    if not q:
        st.warning("Type a question or tap an example above.")
    else:
        with st.spinner("Thinking…"):
            result = ask(q)

        st.subheader("SQL Query")
        st.code(result.get("sql") or "—", language="sql")

        st.subheader("Answer")
        if result.get("ok"):
            st.success(result["answer"])
            rows, rcols = result.get("rows"), result.get("columns")
            if rows:
                st.caption("Raw result")
                st.dataframe(
                    pd.DataFrame(rows, columns=list(rcols)),
                    use_container_width=True,
                    hide_index=True,
                )
            st.session_state.history.append((q, result["sql"]))
        else:
            st.error(result["answer"])

# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------
if st.session_state.history:
    with st.expander("🕘  Question history"):
        for q, sql in reversed(st.session_state.history[-10:]):
            st.markdown(f"**{q}**")
            st.code(sql, language="sql")