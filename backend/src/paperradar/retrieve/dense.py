"""Dense retrieval baseline (BGE-M3 + pgvector cosine similarity).

This is the W1 retrieval baseline. W2 will add BM25 + RRF + reranker.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from paperradar.index.db import connect
from paperradar.index.embed import MODEL_NAME, embed_texts

console = Console()
app = typer.Typer(help="Dense retrieval baseline", no_args_is_help=True)


def search_papers(query_text: str, k: int = 10, venue: str | None = None) -> list[dict[str, Any]]:
    [vec] = embed_texts([query_text])
    arr = np.array(vec, dtype=np.float32)
    sql = """
        SELECT p.forum_id, p.venue, p.title,
               (pe.embedding <=> %s::vector) AS distance
        FROM paper_embeddings pe
        JOIN papers p ON p.forum_id = pe.forum_id
        WHERE pe.model = %s
    """
    args: list[Any] = [arr, MODEL_NAME]
    if venue:
        sql += " AND p.venue = %s"
        args.append(venue)
    sql += " ORDER BY pe.embedding <=> %s::vector LIMIT %s"
    args.extend([arr, k])

    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, args)
        return [
            {"forum_id": fid, "venue": v, "title": t, "distance": float(d)}
            for fid, v, t, d in cur.fetchall()
        ]


def search_reviews(query_text: str, k: int = 10, venue: str | None = None) -> list[dict[str, Any]]:
    [vec] = embed_texts([query_text])
    arr = np.array(vec, dtype=np.float32)
    sql = """
        SELECT r.review_id, r.venue, p.title, r.rating,
               (re.embedding <=> %s::vector) AS distance
        FROM review_embeddings re
        JOIN reviews r ON r.review_id = re.review_id
        JOIN papers p ON p.forum_id = r.forum_id
        WHERE re.model = %s
    """
    args: list[Any] = [arr, MODEL_NAME]
    if venue:
        sql += " AND r.venue = %s"
        args.append(venue)
    sql += " ORDER BY re.embedding <=> %s::vector LIMIT %s"
    args.extend([arr, k])

    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, args)
        return [
            {
                "review_id": rid,
                "venue": v,
                "title": t,
                "rating": rating,
                "distance": float(d),
            }
            for rid, v, t, rating, d in cur.fetchall()
        ]


@app.command()
def papers(
    query: str = typer.Argument(..., help="Free-form text (abstract or excerpt)"),
    k: int = typer.Option(10, help="Top-k"),
    venue: str | None = typer.Option(None, help="Filter by venue"),
) -> None:
    rows = search_papers(query, k=k, venue=venue)
    table = Table(title=f"top-{k} similar papers")
    table.add_column("dist", style="dim", width=6)
    table.add_column("venue", width=12)
    table.add_column("forum_id", width=14)
    table.add_column("title")
    for r in rows:
        table.add_row(f"{r['distance']:.3f}", r["venue"], r["forum_id"], (r["title"] or "")[:90])
    console.print(table)


@app.command()
def reviews(
    query: str = typer.Argument(..., help="Free-form text (a concern, a critique, etc.)"),
    k: int = typer.Option(10, help="Top-k"),
    venue: str | None = typer.Option(None, help="Filter by venue"),
) -> None:
    rows = search_reviews(query, k=k, venue=venue)
    table = Table(title=f"top-{k} similar reviews")
    table.add_column("dist", style="dim", width=6)
    table.add_column("rating", width=6)
    table.add_column("venue", width=12)
    table.add_column("review_id", width=12)
    table.add_column("paper title")
    for r in rows:
        table.add_row(
            f"{r['distance']:.3f}",
            str(r["rating"]) if r["rating"] is not None else "—",
            r["venue"],
            r["review_id"],
            (r["title"] or "")[:80],
        )
    console.print(table)


if __name__ == "__main__":
    app()
