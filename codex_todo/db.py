import duckdb
from pathlib import Path

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
            completed BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

def get_todos(conn):
    return conn.execute(
        "SELECT id, title, completed, created_at FROM todos ORDER BY id"
    ).fetchall()

def add_todo(conn, title):
    conn.execute("INSERT INTO todos (title) VALUES (?);", [title])

def toggle_completed(conn, todo_id):
    conn.execute(
        "UPDATE todos SET completed = NOT completed WHERE id = ?;", [todo_id]
    )

def delete_todo(conn, todo_id):
    conn.execute("DELETE FROM todos WHERE id = ?;", [todo_id])