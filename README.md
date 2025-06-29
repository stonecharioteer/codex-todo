# TODO App

This is a todo app built using python (with uv), textual and should be run using `uvx`. The todos should be written to a duckdb database, and have a configuration that follows
* $XDG_CONFIG_HOME/codex-todo/codex_todo.toml
* $HOME/.codex_todo.toml
* $PWD/.codex_todo.toml
Or use envvars.

The configuration values are:
* `DB_PATH`

## Features

- **Optional due dates** for todos.
- **Calendar picker navigation**: press `c` to show the calendar, use `n`/`p` or `PageDown`/`PageUp` to navigate months, and `Enter` to select a date.
- **Slash-commands for relative dates**: specify due dates inline using slash-commands at the beginning or end of the title:
  - `/today`: today
  - `/tomorrow`: tomorrow
  - `/yesterday`: yesterday
  - `/next-week`: one week from today
  - `/next-month`: one month from today
  - `/next-year`: one year from today
  - `/this-month`: last day of current month
  - `/this-year`: last day of current year
  - `/in-N-days`: N days from today
  - `/in-N-weeks`: N weeks from today
  - `/in-N-months`: N months from today
  - `/in-N-years`: N years from today
- **Absolute date format**: use `YYYY-MM-DD` at the beginning or end of the title.
- **Edit due date**: select a todo, press `e`, then enter a slash-command (e.g. `/tomorrow`), an ISO date (`YYYY-MM-DD`), or leave blank to clear the due date.
- **Confirm deletion**: select a todo, press `d`, then type `y` (or `yes`) to delete or anything else to cancel.

## Demo

Below is an example screen recording (or animated GIF) demonstrating adding, editing, calendar navigation, and confirmation prompts:

![Codex TODO Demo](assets/todo-demo.gif)

### Generating the demo recording

To create or update the animated demo yourself (tested on Ubuntu/Mint), first install the dependencies:
```bash
sudo apt update
sudo apt install -y asciinema 
cargo install --git https://github.com/asciinema/agg
```
Then run the recording script:
```bash
./scripts/record-demo.sh
```
