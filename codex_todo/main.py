
from datetime import date, timedelta
import calendar
import re

from textual.app import App, ComposeResult
from textual.events import Key
from textual.message import Message
from textual.widgets import Header, Footer, Input, DataTable
from textual.containers import Vertical

from .db import (
    get_connection,
    init_db,
    get_todos,
    add_todo,
    toggle_completed,
    delete_todo,
    update_due_date,
)


class CalendarPicker(DataTable):
    """A simple calendar widget for picking a date.

    Navigate months with n/p or PageDown/PageUp, press Enter to select a date.
    """

    class DateSelected(Message):
        """Posted when the user selects a date."""
        def __init__(self, sender: "CalendarPicker", date: date) -> None:
            super().__init__(sender)
            self.date = date

    def __init__(self, year: int, month: int, id: str | None = None) -> None:
        super().__init__(id=id)
        self.year = year
        self.month = month
        self.build_calendar()

    def build_calendar(self) -> None:
        self.clear()
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.add_columns(*days)
        cal = calendar.Calendar(firstweekday=0)
        for week in cal.monthdayscalendar(self.year, self.month):
            self.add_row(*(str(day) if day else "" for day in week))
        self.cursor_type = "cell"
        today = date.today()
        placed = False
        for r, week in enumerate(cal.monthdayscalendar(self.year, self.month)):
            for c, day in enumerate(week):
                if day and (today.year, today.month, today.day) == (self.year, self.month, day):
                    self.cursor_coordinate = (r, c)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            for r, week in enumerate(cal.monthdayscalendar(self.year, self.month)):
                for c, day in enumerate(week):
                    if day:
                        self.cursor_coordinate = (r, c)
                        placed = True
                        break
                if placed:
                    break

    def on_key(self, event: Key) -> None:
        key = event.key.lower()
        if key == "enter":
            r, c = self.cursor_coordinate
            val = self.get_cell_at((r, c))
            if val:
                sel = date(self.year, self.month, int(val))
                self.post_message(self.DateSelected(self, sel))
        elif key in ("n", "pagedown", "page down"):
            if self.month == 12:
                self.month = 1
                self.year += 1
            else:
                self.month += 1
            self.build_calendar()
        elif key in ("p", "pageup", "page up"):
            if self.month == 1:
                self.month = 12
                self.year -= 1
            else:
                self.month -= 1
            self.build_calendar()
        else:
            self.handle_key(event)

class TodoApp(App):
    TITLE = "Codex TODO"
    BINDINGS = [
        ("a", "show_add", "Add Todo"),
        ("t", "toggle_completed", "Toggle Completed"),
        ("d", "delete_todo", "Delete Todo"),
        ("c", "show_calendar", "Set Due Date"),
        ("e", "edit_due", "Edit Due Date"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield DataTable(id="todos")
            yield Input(placeholder="New todo", id="new-todo")
            yield CalendarPicker(date.today().year, date.today().month, id="new-due-date")
        yield Footer()

    def on_mount(self) -> None:
        self.conn = get_connection()
        init_db(self.conn)
        self.todo_table = self.query_one("#todos", DataTable)
        self.todo_table.add_columns("ID", "Title", "Due", "Done", "Created At")
        self.refresh_table()
        self.input = self.query_one("#new-todo", Input)
        self.input.visible = False
        self.calendar = self.query_one("#new-due-date", CalendarPicker)
        self.calendar.visible = False
        self.selected_due_date: date | None = None
        self.editing_id: int | None = None
        self.deleting_id: int | None = None

    def refresh_table(self) -> None:
        self.todo_table.clear()
        for id_, title, due_date, completed, created_at in get_todos(self.conn):
            done = "✅" if completed else ""
            due = due_date.isoformat() if due_date else ""
            self.todo_table.add_row(
                str(id_), title, due, done, str(created_at)
            )

    def action_show_add(self) -> None:
        self.selected_due_date = None
        self.input.placeholder = "New todo"
        self.input.value = ""
        self.input.visible = True
        self.input.focus()

    def action_show_calendar(self) -> None:
        self.input.visible = False
        self.calendar.visible = True
        self.calendar.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        raw = event.value.strip()
        # Confirm deletion if pending
        if self.deleting_id is not None:
            if raw.lower() in ("y", "yes"):
                delete_todo(self.conn, self.deleting_id)
            self.deleting_id = None
            self.input.visible = False
            self.refresh_table()
            return
        # If editing an existing todo's due date, parse raw as relative/ISO and update
        if self.editing_id is not None:
            new_due = self._parse_date_token(raw) if raw else None
            update_due_date(self.conn, self.editing_id, new_due)
            self.refresh_table()
            self.editing_id = None
            self.input.visible = False
            return

        # Otherwise, add a new todo (with optional parsed or calendar-picked due date)
        title, parsed_due = self._parse_title_and_due(raw)
        due = parsed_due or self.selected_due_date
        if title:
            add_todo(self.conn, title, due)
            self.refresh_table()
        self.input.value = ""
        self.input.placeholder = "New todo"
        self.input.visible = False
        self.selected_due_date = None

    def on_calendar_picker_date_selected(
        self, message: CalendarPicker.DateSelected
    ) -> None:
        self.selected_due_date = message.date
        self.calendar.visible = False
        self.input.placeholder = f"New todo (due {self.selected_due_date.isoformat()})"
        self.input.visible = True
        self.input.focus()

    def _parse_title_and_due(self, text: str) -> tuple[str, date | None]:
        """Extract a slash-command or ISO token as due date if present."""
        tokens = text.split()
        if not tokens:
            return "", None
        # Try first token, then last token
        for idx in (0, -1):
            token = tokens[idx]
            parsed = self._parse_date_token(token)
            if parsed:
                # Remove the token from title
                remaining = tokens[1:] if idx == 0 else tokens[:-1]
                return " ".join(remaining).strip(), parsed
        return text, None

    def _parse_date_token(self, token: str) -> date | None:
        t = token.strip()
        today = date.today()
        # Slash commands
        if t.startswith("/"):
            cmd = t[1:]
            low = cmd.lower()
            if low == "today":
                return today
            if low == "tomorrow":
                return today + timedelta(days=1)
            if low == "yesterday":
                return today - timedelta(days=1)
            if low == "next-week":
                return today + timedelta(weeks=1)
            if low == "next-month":
                y, m = today.year, today.month
                if m == 12:
                    ny, nm = y + 1, 1
                else:
                    ny, nm = y, m + 1
                day = min(today.day, calendar.monthrange(ny, nm)[1])
                return date(ny, nm, day)
            if low == "next-year":
                y, m = today.year + 1, today.month
                day = min(today.day, calendar.monthrange(y, m)[1])
                return date(y, m, day)
            if low == "this-month":
                y, m = today.year, today.month
                last = calendar.monthrange(y, m)[1]
                return date(y, m, last)
            if low == "this-year":
                return date(today.year, 12, 31)
            m = re.match(r"in-(\d+)-days$", low)
            if m:
                return today + timedelta(days=int(m.group(1)))
            m = re.match(r"in-(\d+)-weeks$", low)
            if m:
                return today + timedelta(weeks=int(m.group(1)))
            m = re.match(r"in-(\d+)-months$", low)
            if m:
                months = int(m.group(1))
                total = today.month + months
                y = today.year + (total - 1) // 12
                mth = (total - 1) % 12 + 1
                day = min(today.day, calendar.monthrange(y, mth)[1])
                return date(y, mth, day)
            m = re.match(r"in-(\d+)-years$", low)
            if m:
                years = int(m.group(1))
                y = today.year + years
                try:
                    return date(y, today.month, today.day)
                except ValueError:
                    return date(y, today.month, calendar.monthrange(y, today.month)[1])
            # Try ISO date after slash
            try:
                return date.fromisoformat(cmd)
            except ValueError:
                return None
        # ISO date YYYY-MM-DD
        try:
            return date.fromisoformat(t)
        except ValueError:
            return None

    def action_toggle_completed(self) -> None:
        row = self.todo_table.get_row_at(self.todo_table.cursor_row)
        if row:
            todo_id = int(row[0])
            toggle_completed(self.conn, todo_id)
            self.refresh_table()

    def action_delete_todo(self) -> None:
        row = self.todo_table.get_row_at(self.todo_table.cursor_row)
        if not row:
            return
        todo_id = int(row[0])
        title = row[1]
        self.deleting_id = todo_id
        self.input.placeholder = f"Delete '{title}'? (y/n)"
        self.input.value = ""
        self.input.visible = True
        self.input.focus()

    def action_edit_due(self) -> None:
        """Prompt for a new due date (slash-commands or ISO) to update the selected todo."""
        row = self.todo_table.get_row_at(self.todo_table.cursor_row)
        if not row:
            return
        todo_id = int(row[0])
        current_due = row[2] or ""
        prompt = "Set due date"
        if current_due:
            prompt += f" (current {current_due}, leave empty to clear)"
        else:
            prompt += " (slash/ISO, leave empty to clear)"
        self.editing_id = todo_id
        self.input.placeholder = prompt
        self.input.value = ""
        self.input.visible = True
        self.input.focus()

def main() -> None:
    TodoApp().run()

if __name__ == "__main__":
    main()