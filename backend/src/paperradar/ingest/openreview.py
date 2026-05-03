"""OpenReview API ingestion (W1).

Two API generations are in use:
- v1 (legacy): pre-2024 venues, e.g. ICLR 2023 — content fields are plain strings
- v2 (current): 2024+ venues — content fields wrapped as {"value": ...}

Public papers and reviews are accessible without credentials. .env
credentials are optional and only needed for restricted content.

Schema observed for direct replies (both versions):
    Official_Review   — summary / soundness / presentation / contribution /
                        strengths / weaknesses / questions / rating / confidence
    Official_Comment  — title / comment   (typically author rebuttals)
    Meta_Review       — metareview / justification_*  (Area Chair)
    Decision          — title / decision / comment    (Program Chairs)
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

VENUE_CONFIG: dict[str, tuple[str, str]] = {
    "iclr2023": ("v1", "ICLR.cc/2023/Conference/-/Blind_Submission"),
    "iclr2024": ("v2", "ICLR.cc/2024/Conference/-/Submission"),
    "iclr2025": ("v2", "ICLR.cc/2025/Conference/-/Submission"),
    "neurips2024": ("v2", "NeurIPS.cc/2024/Conference/-/Submission"),
}

DEFAULT_OUT_DIR = Path("../data/raw")


def make_client(version: str) -> Any:
    """v1 → openreview.Client, v2 → openreview.api.OpenReviewClient. Anonymous by default."""
    load_dotenv()
    username = os.environ.get("OPENREVIEW_USERNAME")
    password = os.environ.get("OPENREVIEW_PASSWORD")
    if version == "v1":
        return openreview.Client(
            baseurl="https://api.openreview.net",
            username=username,
            password=password,
        )
    return openreview.api.OpenReviewClient(
        baseurl="https://api2.openreview.net",
        username=username,
        password=password,
    )


def note_to_dict(n: Any) -> dict[str, Any]:
    """Serialize a Note (v1 or v2) to a JSON-safe dict."""
    return {
        "id": n.id,
        "forum": n.forum,
        "invitations": getattr(n, "invitations", None) or [getattr(n, "invitation", None)],
        "signatures": n.signatures,
        "content": n.content,
        "details": n.details,
        "cdate": getattr(n, "cdate", None),
        "mdate": getattr(n, "mdate", None),
    }


def get_title(content: dict[str, Any] | None) -> str:
    """v2 wraps values as {value: ...}; v1 stores them directly."""
    title = (content or {}).get("title", "<no title>")
    if isinstance(title, dict):
        return title.get("value", "<no title>")
    return str(title)


def reply_kind(reply: dict[str, Any]) -> str:
    """Classify a reply by its invitation suffix.

    v2 reply has 'invitations' (list); v1 has 'invitation' (string).
    v2 paper-level invitations look like  .../Submission1647/-/Official_Review
    v1 paper-level invitations look like  .../Paper3283/-/Official_Review
    """
    invitations = reply.get("invitations") or [reply.get("invitation")]
    for inv in invitations:
        if not inv or "/-/" not in inv:
            continue
        suffix = inv.rsplit("/-/", 1)[-1]
        if suffix in {"Official_Review", "Official_Comment", "Meta_Review", "Decision"}:
            return suffix
    return "?"


@app.command()
def explore(venue: str = typer.Option("iclr2024", help="Venue key")) -> None:
    """Pull 1 submission + replies; print a high-level summary."""
    if venue not in VENUE_CONFIG:
        raise typer.BadParameter(f"unknown venue '{venue}'")
    version, invitation = VENUE_CONFIG[venue]

    client = make_client(version)
    console.print(f"[bold cyan]venue:[/] {venue}  api={version}  invitation: {invitation}")

    notes = client.get_notes(invitation=invitation, details="directReplies", limit=1)
    if not notes:
        console.print("[red]no notes returned[/]")
        raise typer.Exit(1)

    n = notes[0]
    console.print(f"[bold green]submission:[/] id={n.id}  title={get_title(n.content)!r}")
    console.print(f"  content keys: {list((n.content or {}).keys())}")

    replies = (n.details or {}).get("directReplies", []) or []
    console.print(f"[bold]direct replies: {len(replies)}[/]")
    for r in replies:
        kind = reply_kind(r)
        sigs = r.get("signatures") or []
        sig = sigs[0].rsplit("/", 1)[-1] if sigs else "?"
        keys = list((r.get("content") or {}).keys())
        console.print(f"  - {kind:<18} signed_by={sig:<28} content_keys={keys}")


def _fetch_one(venue: str, limit: int | None, out_dir: Path) -> int:
    """Implementation shared by fetch / fetch_all. Returns number written."""
    if venue not in VENUE_CONFIG:
        raise typer.BadParameter(f"unknown venue '{venue}'")
    version, invitation = VENUE_CONFIG[venue]

    client = make_client(version)
    console.print(f"[bold]fetching[/] {venue}  api={version}  invitation={invitation}")

    notes = client.get_all_notes(invitation=invitation, details="directReplies")
    console.print(f"  total available: {len(notes)}")
    if limit is not None:
        notes = notes[:limit]
        console.print(f"  capped to: {len(notes)}")

    out = out_dir / venue
    out.mkdir(parents=True, exist_ok=True)
    submissions_file = out / "submissions.jsonl"
    with submissions_file.open("w") as f:
        for n in notes:
            f.write(json.dumps(note_to_dict(n)) + "\n")

    console.print(f"[green]wrote {len(notes)} → {submissions_file}[/]")
    return len(notes)


@app.command()
def fetch(
    venue: str = typer.Option(..., help="Venue key"),
    limit: int | None = typer.Option(None, help="Optional cap; omit for full fetch"),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Output dir"),
) -> None:
    """Fetch submissions + direct replies, write raw JSONL to {out_dir}/{venue}/."""
    _fetch_one(venue, limit, out_dir)


@app.command()
def fetch_all(
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR, help="Output dir"),
) -> None:
    """Fetch all configured venues into {out_dir}/{venue}/submissions.jsonl."""
    totals: dict[str, int] = {}
    for venue in VENUE_CONFIG:
        console.rule(f"[bold]{venue}[/]")
        totals[venue] = _fetch_one(venue, None, out_dir)
    console.rule("[bold]summary[/]")
    for v, n in totals.items():
        console.print(f"  {v:<12} {n:>6}")
    console.print(f"  {'TOTAL':<12} {sum(totals.values()):>6}")


if __name__ == "__main__":
    app()
