import os
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

def load_config():
    """Load configuration from TOML files or environment variable."""
    config = {}
    xdg_home = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    paths = [
        Path(xdg_home) / "codex-todo" / "codex_todo.toml",
        Path.home() / ".codex_todo.toml",
        Path.cwd() / ".codex_todo.toml",
    ]
    for path in paths:
        if path.is_file():
            with path.open("rb") as f:
                data = tomllib.load(f)
            config.update(data)
    db_env = os.environ.get("DB_PATH")
    if db_env:
        config["DB_PATH"] = db_env
    if not config.get("DB_PATH"):
        raise RuntimeError("DB_PATH must be set via config file or DB_PATH environment variable")
    return config