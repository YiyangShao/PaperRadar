"""Load processed JSONL into Postgres via COPY (fast bulk insert).

CLI:
  init                 — create tables + basic indexes (idempotent)
  load --venue X       — load papers/reviews/meta_reviews for one venue
  load-all             — load all configured venues
  build-vector-indexes — create HNSW indexes (run after embeddings are loaded)
  stats                — print row counts
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from paperradar.index.db import connect, init_schema
from paperradar.ingest.openreview import VENUE_CONFIG

console = Console()
app = typer.Typer(help="Load processed data into Postgres", no_args_is_help=True)

DEFAULT_PROCESSED = Path("../data/processed")

PAPER_COLS = [
    "forum_id", "raw_id", "venue", "api_version", "title", "abstract",
    "authors", "keywords", "primary_area", "pdf_url", "is_withdrawn",
]
REVIEW_COLS = [
    "review_id", "forum_id", "venue", "api_version", "reviewer_handle",
    "rating", "confidence", "summary", "strengths", "weaknesses", "questions",
    "overall_verdict", "soundness", "presentation", "contribution",
    "correctness", "technical_novelty", "empirical_novelty",
    "review_text",
]
META_COLS = [
    "meta_id", "forum_id", "venue", "api_version",
    "metareview", "decision", "why_not_higher", "why_not_lower",
]


def _strip_nul(v: Any) -> Any:
    """Postgres text/jsonb cannot contain NUL bytes; reviewers occasionally paste them."""
    if isinstance(v, str):
        return v.replace("\x00", "")
    if isinstance(v, dict):
        return {k: _strip_nul(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_strip_nul(x) for x in v]
    return v


def stream_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield _strip_nul(json.loads(line))


def copy_rows(conn: Any, table: str, cols: list[str], rows: Iterator[tuple]) -> int:
    """Bulk-load rows via Postgres COPY. Caller provides tuples in column order."""
    n = 0
    with conn.cursor() as cur:
        with cur.copy(f"COPY {table} ({','.join(cols)}) FROM STDIN") as cp:
            for row in rows:
                cp.write_row(row)
                n += 1
    return n


def paper_rows(path: Path) -> Iterator[tuple]:
    for r in stream_jsonl(path):
        yield (
            r["forum_id"], r["raw_id"], r["venue"], r["api_version"],
            r["title"], r["abstract"],
            r["authors"], r["keywords"],
            r.get("primary_area"), r.get("pdf_url"),
            r["is_withdrawn"],
        )


def review_rows(path: Path) -> Iterator[tuple]:
    for r in stream_jsonl(path):
        yield (
            r["review_id"], r["forum_id"], r["venue"], r["api_version"],
            r["reviewer_handle"], r.get("rating"), r.get("confidence"),
            r.get("summary"), r.get("strengths"), r.get("weaknesses"),
            r.get("questions"), r.get("overall_verdict"),
            r.get("soundness"), r.get("presentation"), r.get("contribution"),
            r.get("correctness"), r.get("technical_novelty"), r.get("empirical_novelty"),
            r["review_text"],
        )


def meta_rows(path: Path) -> Iterator[tuple]:
    for r in stream_jsonl(path):
        yield (
            r["meta_id"], r["forum_id"], r["venue"], r["api_version"],
            r.get("metareview"), r.get("decision"),
            r.get("why_not_higher"), r.get("why_not_lower"),
        )


def _load_venue(venue: str, processed_dir: Path) -> dict[str, int]:
    base = processed_dir / venue
    out: dict[str, int] = {}
    with connect() as conn:
        out["papers"] = copy_rows(conn, "papers", PAPER_COLS, paper_rows(base / "papers.jsonl"))
        out["reviews"] = copy_rows(conn, "reviews", REVIEW_COLS, review_rows(base / "reviews.jsonl"))
        out["meta_reviews"] = copy_rows(conn, "meta_reviews", META_COLS, meta_rows(base / "meta_reviews.jsonl"))
        conn.commit()
    return out


@app.command()
def init() -> None:
    """Create tables + indexes (idempotent)."""
    init_schema()
    console.print("[green]schema initialized[/]")


@app.command()
def load(
    venue: str = typer.Option(..., help="Venue key"),
    processed_dir: Path = typer.Option(DEFAULT_PROCESSED),
) -> None:
    """Load one venue. Assumes schema exists and tables are empty for that venue."""
    if venue not in VENUE_CONFIG:
        raise typer.BadParameter(f"unknown venue '{venue}'")
    counts = _load_venue(venue, processed_dir)
    console.print(f"[green]{venue}[/]  " + "  ".join(f"{k}={v}" for k, v in counts.items()))


@app.command()
def load_all(
    processed_dir: Path = typer.Option(DEFAULT_PROCESSED),
) -> None:
    """Load every configured venue."""
    grand: dict[str, int] = {"papers": 0, "reviews": 0, "meta_reviews": 0}
    for venue in VENUE_CONFIG:
        console.rule(f"[bold]{venue}[/]")
        counts = _load_venue(venue, processed_dir)
        for k, v in counts.items():
            grand[k] += v
        console.print("  " + "  ".join(f"{k}={v}" for k, v in counts.items()))
    console.rule("[bold]total[/]")
    console.print("  " + "  ".join(f"{k}={v}" for k, v in grand.items()))


@app.command()
def stats() -> None:
    """Print row counts per table."""
    queries = {
        "papers": "SELECT venue, COUNT(*) FROM papers GROUP BY venue ORDER BY venue",
        "reviews": "SELECT venue, COUNT(*) FROM reviews GROUP BY venue ORDER BY venue",
        "meta_reviews": "SELECT venue, COUNT(*) FROM meta_reviews GROUP BY venue ORDER BY venue",
        "paper_embeddings": "SELECT model, COUNT(*) FROM paper_embeddings GROUP BY model",
        "review_embeddings": "SELECT model, COUNT(*) FROM review_embeddings GROUP BY model",
    }
    with connect() as conn:
        with conn.cursor() as cur:
            for name, q in queries.items():
                cur.execute(q)
                rows = cur.fetchall()
                console.print(f"[bold]{name}[/]: {rows or '(empty)'}")


@app.command()
def build_vector_indexes() -> None:
    """Create HNSW indexes after bulk-loading embeddings.

    HNSW with cosine distance is the standard pgvector choice for ANN search.
    """
    sqls = [
        "CREATE INDEX IF NOT EXISTS paper_emb_hnsw ON paper_embeddings "
        "USING hnsw (embedding vector_cosine_ops)",
        "CREATE INDEX IF NOT EXISTS review_emb_hnsw ON review_embeddings "
        "USING hnsw (embedding vector_cosine_ops)",
    ]
    with connect(autocommit=True) as conn:
        with conn.cursor() as cur:
            for sql in sqls:
                console.print(f"running: {sql.split(' ON ')[1].split(' ')[0]}")
                cur.execute(sql)
    console.print("[green]vector indexes built[/]")


if __name__ == "__main__":
    app()
