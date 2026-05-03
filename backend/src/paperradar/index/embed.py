"""BGE-M3 dense embeddings → pgvector.

Why BGE-M3:
- Strong English+multilingual performance, competitive with OpenAI
  text-embedding-3-large on MTEB Retrieval
- 1024-dim dense vectors (also supports sparse + ColBERT-style multi-vec,
  not used here)
- Runs locally; no API cost; first run downloads ~2GB to ~/.cache/

CLI:
  embed-papers   --venue X [--limit N]
  embed-reviews  --venue X [--limit N]
  embed-all                          run papers + reviews for all venues
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Any

import numpy as np
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from paperradar.index.db import connect
from paperradar.ingest.openreview import VENUE_CONFIG

console = Console()
app = typer.Typer(help="BGE-M3 embeddings → pgvector", no_args_is_help=True)

MODEL_NAME = "bge-m3"
BATCH_SIZE = 32
EMBED_DIM = 1024


_model: Any = None


def get_model() -> Any:
    """Lazy-load BGE-M3 once per process."""
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        console.print("[dim]loading BGE-M3 (first run downloads ~2GB)...[/]")
        _model = TextEmbedding(model_name="BAAI/bge-m3")
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return a 1024-dim embedding per input. fastembed yields generators."""
    return [v.tolist() for v in get_model().embed(texts)]


def chunked(it: Iterable[Any], n: int) -> Iterator[list[Any]]:
    buf: list[Any] = []
    for x in it:
        buf.append(x)
        if len(buf) >= n:
            yield buf
            buf = []
    if buf:
        yield buf


def _fetch_paper_targets(
    conn: Any, venue: str | None, limit: int | None
) -> list[tuple[str, str]]:
    """Return (forum_id, text) tuples for papers not yet embedded by MODEL_NAME."""
    sql = """
        SELECT p.forum_id, COALESCE(p.title || E'\n\n' || p.abstract, p.title)
        FROM papers p
        LEFT JOIN paper_embeddings pe
            ON pe.forum_id = p.forum_id AND pe.model = %s
        WHERE pe.forum_id IS NULL
    """
    args: list[Any] = [MODEL_NAME]
    if venue:
        sql += " AND p.venue = %s"
        args.append(venue)
    sql += " ORDER BY p.forum_id"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def _fetch_review_targets(
    conn: Any, venue: str | None, limit: int | None
) -> list[tuple[str, str]]:
    sql = """
        SELECT r.review_id, r.review_text
        FROM reviews r
        LEFT JOIN review_embeddings re
            ON re.review_id = r.review_id AND re.model = %s
        WHERE re.review_id IS NULL
    """
    args: list[Any] = [MODEL_NAME]
    if venue:
        sql += " AND r.venue = %s"
        args.append(venue)
    sql += " ORDER BY r.review_id"
    if limit:
        sql += f" LIMIT {int(limit)}"
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()


def _write_embeddings(
    conn: Any, table: str, key_col: str, rows: list[tuple[str, list[float]]]
) -> None:
    """Insert (id, embedding) pairs with model=MODEL_NAME, ON CONFLICT skip."""
    sql = (
        f"INSERT INTO {table} ({key_col}, model, embedding) "
        f"VALUES (%s, %s, %s) "
        f"ON CONFLICT ({key_col}, model) DO NOTHING"
    )
    payload = [(rid, MODEL_NAME, np.array(v, dtype=np.float32)) for rid, v in rows]
    with conn.cursor() as cur:
        cur.executemany(sql, payload)


def _run(
    targets: list[tuple[str, str]],
    table: str,
    key_col: str,
    label: str,
) -> int:
    if not targets:
        console.print(f"[yellow]{label}: nothing to embed[/]")
        return 0

    n_done = 0
    with connect() as conn, Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as bar:
        task = bar.add_task(label, total=len(targets))
        for batch in chunked(targets, BATCH_SIZE):
            ids = [r[0] for r in batch]
            texts = [r[1] for r in batch]
            vecs = embed_texts(texts)
            _write_embeddings(conn, table, key_col, list(zip(ids, vecs, strict=True)))
            conn.commit()
            n_done += len(batch)
            bar.update(task, advance=len(batch))
    return n_done


@app.command()
def embed_papers(
    venue: str | None = typer.Option(None, help="Restrict to one venue"),
    limit: int | None = typer.Option(None, help="Cap how many to embed"),
) -> None:
    """Embed paper title+abstract → paper_embeddings."""
    with connect() as conn:
        targets = _fetch_paper_targets(conn, venue, limit)
    n = _run(targets, "paper_embeddings", "forum_id", "papers")
    console.print(f"[green]embedded {n} papers[/]")


@app.command()
def embed_reviews(
    venue: str | None = typer.Option(None, help="Restrict to one venue"),
    limit: int | None = typer.Option(None, help="Cap how many to embed"),
) -> None:
    """Embed full review_text → review_embeddings."""
    with connect() as conn:
        targets = _fetch_review_targets(conn, venue, limit)
    n = _run(targets, "review_embeddings", "review_id", "reviews")
    console.print(f"[green]embedded {n} reviews[/]")


@app.command()
def embed_all() -> None:
    """Embed papers then reviews across all venues. Resumable: skips rows
    already embedded under the same model name."""
    for venue in VENUE_CONFIG:
        console.rule(f"[bold]{venue}[/] papers")
        with connect() as conn:
            t = _fetch_paper_targets(conn, venue, None)
        _run(t, "paper_embeddings", "forum_id", f"{venue}/papers")
    for venue in VENUE_CONFIG:
        console.rule(f"[bold]{venue}[/] reviews")
        with connect() as conn:
            t = _fetch_review_targets(conn, venue, None)
        _run(t, "review_embeddings", "review_id", f"{venue}/reviews")


if __name__ == "__main__":
    app()
