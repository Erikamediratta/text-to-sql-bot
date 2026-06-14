#Give me the database connection, and don't care whether the project is using SQLite or MySQL

import os
from sqlalchemy import create_engine
#create_engine()_> SQLAlchemy function that creates a database connection

# Use DATABASE_URL if it exists.
# Otherwise use SQLite.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///company.db"
)
# Create a Connection 

def get_engine():
    return create_engine(DATABASE_URL)

# Check which database is being used 
#print(dialect_name()) give output-> SQLite or MySQL

def dialect_name():
    return get_engine().dialect.name