import re

FORBIDDEN = [
    "drop",
    "delete",
    "update",
    "insert"
]

def is_safe_sql(sql):
    sql=sql.lower()

    for word in FORBIDDEN:
        if word in sql:
            return False
    return True

# Very important file as User question->LLM generates SQL -> this file checks SQL->
# if its safe, run, else->block
# ,
# WITHOUT THIS, the LLM might generate drop table customers and destroy the database

