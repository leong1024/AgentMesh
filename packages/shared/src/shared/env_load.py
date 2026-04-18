"""Load `.env` for local development (does not override existing variables)."""

from __future__ import annotations


def load_local_env() -> None:
    """Populate ``os.environ`` from a nearest `.env` file (walks up from cwd)."""
    from dotenv import find_dotenv, load_dotenv

    path = find_dotenv(usecwd=True)
    if path:
        load_dotenv(path, override=False)
