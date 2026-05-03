"""Postgres connection helpers."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

SCHEMA_FILE = Path(__file__).parent / "schema.sql"


def get_db_url() -> str:
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL not set in environment / .env")
    return url


@contextmanager
def connect(autocommit: bool = False, register_vec: bool = True) -> Iterator[Any]:
    """Open a connection. register_vec=False during initial schema creation
    (the vector type may not exist yet)."""
    with psycopg.connect(get_db_url(), autocommit=autocommit) as conn:
        if register_vec:
            register_vector(conn)
        yield conn


def init_schema() -> None:
    sql = SCHEMA_FILE.read_text()
    with connect(autocommit=True, register_vec=False) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
