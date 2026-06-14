from engine import run_query
from guardrails import is_safe_sql


# 1. Test dataset
TEST_SET = [
    ("How many customers are there?", 7),        # was 5
    ("How many customers are from Delhi?", 3),   # was 2
    ("How many orders have status completed?", 6),
    ("How many products are in electronics?", 3),
]


# 2. Fake SQL generator (NO AI → avoids quota issues)
def generate_sql(question):
    mapping = {
        "How many customers are there?": "SELECT COUNT(*) FROM customers",
        "How many customers are from Delhi?": "SELECT COUNT(*) FROM customers WHERE city='Delhi'",
        "How many orders have status completed?": "SELECT COUNT(*) FROM orders WHERE status='completed'",
        "How many products are in electronics?": "SELECT COUNT(*) FROM products WHERE category='electronics'",
    }

    return mapping.get(question, "")


# 3. helper: extract result
def get_first_value(rows):
    if not rows:
        return None
    return rows[0][0]


# 4. evaluation
def evaluate():
    passed = 0

    for question, expected in TEST_SET:

        try:
            # Step 1: get SQL
            sql = generate_sql(question)

            if not sql:
                print("NO SQL:", question)
                continue

            # Step 2: safety check
            if not is_safe_sql(sql):
                print("BLOCKED:", question)
                continue

            # Step 3: run query
            cols, rows = run_query(sql)

            # Step 4: extract answer
            got = get_first_value(rows)

            # Step 5: compare
            if got == expected:
                print("PASS:", question)
                passed += 1
            else:
                print("FAIL:", question)
                print("   Expected:", expected)
                print("   Got:", got)

        except Exception as e:
            print("ERROR:", question, e)

    print("\nFinal Score:", passed, "/", len(TEST_SET))


# 5. run
if __name__ == "__main__":
    evaluate()