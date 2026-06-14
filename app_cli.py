from engine import ask
# connects to main brain
# english-> SQL-> DB-> english

MAX_MEMORY_TURNS = 3
#keep only last 3 conversations

# Convert chat history into text format
def format_history(turns):
    result = ""

    for q, sql in turns:
        result += "Q: " + q + "\n"
        result += "SQL: " + sql + "\n\n"

    return result.strip()


def main():
    print("Text-to-SQL Chatbot (CLI)")
    print("Type 'exit' to quit, '/reset' to clear memory\n")

    history = []

    while True:
        question = input("Ask a question: ")

        if question.lower() =="exit":
            break

        if question == "/reset":
            history = []
            print("Memory cleared\n")
            continue

        # last 3 turns only
        ctx = format_history(history[-MAX_MEMORY_TURNS:])

        # ask engine (LLM + SQL pipeline)
        result = ask(question,history=ctx)

        print("\nSQL:", result["sql"])
        print("Answer:", result["answer"], "\n")

        # store only successful queries
        if result["ok"]:
            history.append((question, result["sql"]))


if __name__ == "__main__":
    main()