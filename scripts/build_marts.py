import sqlite3
import os

DB_PATH = os.path.join("data", "f1_fantasy.db")
SQL_PATH = os.path.join("sql", "create_value_marts.sql")

def main():
    
    with sqlite3.connect(DB_PATH) as con:
        with open(SQL_PATH, "r") as file:
            sql_script = file.read()

        con.executescript(sql_script)

    print("Marts created successfully.")


if __name__ == "__main__":
    main()