from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, DataTable
from textual.containers import Vertical

from .db import get_connection, init_db, get_todos, add_todo, toggle_completed, delete_todo

class TodoApp(App):
    TITLE = "Codex TODO"
    BINDINGS = [
        ("a", "show_add", "Add Todo"),
        ("t", "toggle_completed", "Toggle Completed"),
        ("d", "delete_todo", "Delete Todo"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield DataTable(id="todos")
            yield Input(placeholder="New todo", id="new-todo")
        yield Footer()

    def on_mount(self) -> None:
        self.conn = get_connection()
        init_db(self.conn)
        self.todo_table = self.query_one("#todos", DataTable)
        self.todo_table.add_columns("ID", "Title", "Done", "Created At")
        self.refresh_table()
        self.input = self.query_one("#new-todo", Input)
        self.input.visible = False

    def refresh_table(self) -> None:
        self.todo_table.clear()
        for id_, title, completed, created_at in get_todos(self.conn):
            done = "✅" if completed else ""
            self.todo_table.add_row(str(id_), title, done, str(created_at))

    def action_show_add(self) -> None:
        self.input.visible = True
        self.input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        title = event.value.strip()
        if title:
            add_todo(self.conn, title)
            self.refresh_table()
        self.input.value = ""
        self.input.visible = False

    def action_toggle_completed(self) -> None:
        row = self.todo_table.get_row_at(self.todo_table.cursor_row)
        if row:
            todo_id = int(row[0])
            toggle_completed(self.conn, todo_id)
            self.refresh_table()

    def action_delete_todo(self) -> None:
        row = self.todo_table.get_row_at(self.todo_table.cursor_row)
        if row:
            todo_id = int(row[0])
            delete_todo(self.conn, todo_id)
            self.refresh_table()

def main() -> None:
    TodoApp().run()

if __name__ == "__main__":
    main()