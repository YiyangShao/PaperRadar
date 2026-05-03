"""OpenReview API ingestion (W1).

API v2 docs: https://docs.openreview.net/getting-started/using-the-api

Verified 2026-05-03 (W1-D1): public papers and reviews are accessible
without authentication. Credentials are optional and only needed for
restricted content (which we do not ingest).

Schema observed for ICLR 2024 submissions:
- submission.content      : title, abstract, authors, authorids, keywords,
                            primary_area, pdf, _bibtex, paperhash, venue, venueid
                            (all values are wrapped as {"value": ...} in API v2)
- details.directReplies[] : 4 distinct reply types, identified by invitation suffix
    - Official_Review     : summary, soundness, presentation, contribution,
                            strengths, weaknesses, questions, rating, confidence
    - Official_Comment    : title, comment   (typically author rebuttals)
    - Meta_Review         : metareview, justification_for_why_(not_)higher/lower_score
    - Decision            : title, decision, comment   (Program Chairs)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import openreview
import typer
from dotenv import load_dotenv
from rich.console import Console

console = Console()
app = typer.Typer(help="OpenReview ingestion (W1)", no_args_is_help=True)

VENUE_SUBMISSION_INVITATIONS: dict[str, str] = {
    "iclr2023": "ICLR.cc/2023/Conference/-/Blind_Submission",
    "iclr2024": "ICLR.cc/2024/Conference/-/Submission",
    "iclr2025": "ICLR.cc/2025/Conference/-/Submission",
    "neurips2024": "NeurIPS.cc/2024/Conference/-/Submission",
}

DEFAULT_OUT_DIR = Path("../data/raw")


def make_client() -> Any:
    """Build a v2 client. Anonymous by default; uses .env credentials if present."""
    load_dotenv()
    username = os.environ.get("OPENREVIEW_USERNAME")
    password = os.environ.get("OPENREVIEW_PASSWORD")
    if username and password:
        return openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net",
            username=username,
            password=password,
        )
    return openreview.api.OpenReviewClient(baseurl="https://api2.openreview.net")


def note_to_dict(n: Any) -> dict[str, Any]:
    """Serialize a v2 Note to a JSON-safe dict (Note objects don't expose to_json)."""
    return {
        "id": n.id,
        "forum": n.forum,
        "invitations": n.invitations,
        "signatures": n.signatures,
        "content": n.content,
        "details": n.details,
        "cdate": n.cdate,
        "mdate": n.mdate,
    }


def reply_kind(reply: dict[str, Any]) -> str:
    """Extract the reply type from its invitation suffix."""
    for inv in reply.get("invitations", []):
        if "/Submission" in inv and "/-/" in inv:
            suffix = inv.rsplit("/-/", 1)[1]
            if suffix in {"Official_Review", "Official_Comment", "Meta_Review", "Decision"}:
                return suffix
    return "?"


@app.command()
def explore(venue: str = typer.Option("iclr2024", help="Venue key")) -> None:
    """Pull 1 submission + its replies; print a high-level summary."""
    if venue not in VENUE_SUBMISSION_INVITATIONS:
        raise typer.BadParameter(f"unknown venue '{venue}'")

    client = make_client()
    invitation = VENUE_SUBMISSION_INVITATIONS[venue]
    console.print(f"[bold cyan]venue:[/] {venue}  invitation: {invitation}")

    notes = client.get_notes(invitation=invitation, details="directReplies", limit=1)
    if not notes:
        console.print("[red]no notes returned[/]")
        raise typer.Exit(1)

    n = notes[0]
    title = (n.content or {}).get("title", {}).get("value", "<no title>")
    console.print(f"[bold green]submission:[/] id={n.id}  title={title!r}")
    console.print(f"  content keys: {list((n.content or {}).keys())}")

    replies = (n.details or {}).get("directReplies", []) or []
    console.print(f"[bold]direct replies: {len(replies)}[/]")
    for r in replies:
        kind = reply_kind(r)
        sigs = r.get("signatures") or []
        sig = sigs[0].rsplit("/", 1)[-1] if sigs else "?"
        keys = list((r.get("content") or {}).keys())
        console.print(f"  - {kind:<18} signed_by={sig:<28} content_keys={keys}")


@app.command()
def fetch(
    venue: str = typer.Option(..., help="Venue key"),
    limit: int = typer.Option(5, help="Cap on submissions"),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Output dir"),
) -> None:
    """Fetch N submissions + direct replies, write raw JSONL to {out_dir}/{venue}/."""
    if venue not in VENUE_SUBMISSION_INVITATIONS:
        raise typer.BadParameter(f"unknown venue '{venue}'")

    client = make_client()
    invitation = VENUE_SUBMISSION_INVITATIONS[venue]
    console.print(f"[bold]fetching[/] {venue}  invitation={invitation}  limit={limit}")

    notes = client.get_all_notes(invitation=invitation, details="directReplies")
    console.print(f"  total available: {len(notes)}")
    notes = notes[:limit]

    out = out_dir / venue
    out.mkdir(parents=True, exist_ok=True)
    submissions_file = out / "submissions.jsonl"
    with submissions_file.open("w") as f:
        for n in notes:
            f.write(json.dumps(note_to_dict(n)) + "\n")

    console.print(f"[green]wrote {len(notes)} → {submissions_file}[/]")


if __name__ == "__main__":
    app()
