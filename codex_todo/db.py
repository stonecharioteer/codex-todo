import duckdb
from pathlib import Path
from datetime import date

from .config import load_config

def get_connection():
    cfg = load_config()
    db_path = Path(cfg["DB_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db_path))

def init_db(conn):
    conn.execute(
        """
        CREATE SEQUENCE IF NOT EXISTS todos_seq;
        CREATE TABLE IF NOT EXISTS todos (
            id BIGINT NOT NULL DEFAULT nextval('todos_seq'),
            title TEXT NOT NULL,
            due_date DATE,
            completed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        ALTER TABLE todos ADD COLUMN IF NOT EXISTS due_date DATE;
        """
    )

def get_todos(conn):
    return conn.execute(
        "SELECT id, title, due_date, completed, created_at"
        " FROM todos ORDER BY id"
    ).fetchall()

def add_todo(conn, title, due_date=None):
    if due_date is not None:
        conn.execute(
            "INSERT INTO todos (title, due_date) VALUES (?, ?);",
            [title, due_date],
        )
    else:
        conn.execute("INSERT INTO todos (title) VALUES (?);", [title])

def toggle_completed(conn, todo_id):
    conn.execute(
        "UPDATE todos SET completed = NOT completed WHERE id = ?;", [todo_id]
    )

def delete_todo(conn, todo_id):
    conn.execute("DELETE FROM todos WHERE id = ?;", [todo_id])

def update_due_date(conn, todo_id: int, due_date: date | None):
    """Set or clear the due_date for an existing todo."""
    if due_date is not None:
        conn.execute(
            "UPDATE todos SET due_date = ? WHERE id = ?;",
            [due_date, todo_id],
        )
    else:
        conn.execute(
            "UPDATE todos SET due_date = NULL WHERE id = ?;",
            [todo_id],
        )