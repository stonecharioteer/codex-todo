# TODO App

This is a todo app built using python (with uv), textual and should be run using `uvx`. The todos should be written to a duckdb database, and have a configuration that follows
* $XDG_CONFIG_HOME/codex-todo/codex_todo.toml
* $HOME/.codex_todo.toml
* $PWD/.codex_todo.toml
Or use envvars.

The configuration values are:
* DB_PATH

I'll add more features as I go along.
