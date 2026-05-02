"""OpenReview API ingestion (W1).

W1-D1: validate API access on a single submission.
W1-D2+: scale to full venue ingestion into data/raw/{venue}/.

API v2 docs: https://docs.openreview.net/getting-started/using-the-api
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.pretty import pprint

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
    """Build an OpenReview API v2 client. Requires .env credentials."""
    import openreview  # imported here so --help works without the package

    load_dotenv()
    username = os.environ["OPENREVIEW_USERNAME"]
    password = os.environ["OPENREVIEW_PASSWORD"]
    return openreview.api.OpenReviewClient(
        baseurl="https://api2.openreview.net",
        username=username,
        password=password,
    )


@app.command()
def explore(venue: str = typer.Option("iclr2024", help="Venue key")) -> None:
    """Pull 1 submission + replies and pretty-print its structure for inspection."""
    if venue not in VENUE_SUBMISSION_INVITATIONS:
        raise typer.BadParameter(
            f"unknown venue '{venue}'. valid: {list(VENUE_SUBMISSION_INVITATIONS)}"
        )

    client = make_client()
    invitation = VENUE_SUBMISSION_INVITATIONS[venue]
    console.print(f"[bold cyan]venue:[/] {venue}  invitation: {invitation}")

    notes = client.get_notes(invitation=invitation, details="directReplies", limit=1)
    if not notes:
        console.print("[red]no notes returned — check invitation string and credentials[/]")
        raise typer.Exit(1)

    note = notes[0]
    payload = note.to_json()
    console.print("[bold green]first note (truncated):[/]")
    pprint(payload, max_string=200)

    replies = payload.get("details", {}).get("directReplies", []) or []
    console.print(f"\n[bold]direct replies count:[/] {len(replies)}")
    if replies:
        console.print("[bold]first reply preview:[/]")
        pprint(replies[0], max_string=200)


@app.command()
def fetch(
    venue: str = typer.Option(..., help="Venue key"),
    limit: int = typer.Option(5, help="Cap on submissions (W1 default = 5)"),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Output dir relative to cwd"),
) -> None:
    """Fetch N submissions + direct replies and write to {out_dir}/{venue}/submissions.jsonl."""
    if venue not in VENUE_SUBMISSION_INVITATIONS:
        raise typer.BadParameter(
            f"unknown venue '{venue}'. valid: {list(VENUE_SUBMISSION_INVITATIONS)}"
        )

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
        for note in notes:
            f.write(json.dumps(note.to_json()) + "\n")

    console.print(f"[green]wrote {len(notes)} submissions → {submissions_file}[/]")


if __name__ == "__main__":
    app()
