
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

load_dotenv()

database_url = os.getenv("DATABASE_URL")

engine = create_engine(database_url)

with engine.connect() as conn:
    print("SQLite connected successfully!")

    tables = inspect(engine).get_table_names()
    print("Available tables:", tables)

    if "cit_national_ranks" in tables:
        count = conn.execute(
            text('SELECT COUNT(*) FROM "cit_national_ranks"')
        ).scalar_one()

        columns = inspect(engine).get_columns("cit_national_ranks")

        print("Dataset records:", count)
        print("Number of columns:", len(columns))
        print("Column names:", [c["name"] for c in columns])
    else:
        print("Dataset table has not been created yet.")
