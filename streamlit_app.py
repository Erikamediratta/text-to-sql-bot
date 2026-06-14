import streamlit as st
from engine import ask

st.set_page_config(page_title="Text-to-SQL Bot", page_icon="🧠")

st.title("🧠 Text-to-SQL Chatbot")

st.write("Ask questions about your database")

# session memory
if "history" not in st.session_state:
    st.session_state.history = []

question = st.text_input("Enter your question")

if st.button("Ask") and question:
    result = ask(question)

    st.subheader("SQL Query")
    st.code(result["sql"], language="sql")

    st.subheader("Answer")
    st.write(result["answer"])

    # store history
    if result["ok"]:
        st.session_state.history.append((question, result["sql"]))