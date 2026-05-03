"""Normalize raw OpenReview notes (v1 + v2) into unified models.

Reads:  data/raw/{venue}/submissions.jsonl     (one submission per line + replies)
Writes: data/processed/{venue}/papers.jsonl
        data/processed/{venue}/reviews.jsonl
        data/processed/{venue}/meta_reviews.jsonl
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from paperradar.ingest.openreview import VENUE_CONFIG, reply_kind
from paperradar.normalize.models import MetaReview, Paper, Review

console = Console()
app = typer.Typer(help="Normalize raw OpenReview notes (W1)", no_args_is_help=True)

DEFAULT_RAW_DIR = Path("../data/raw")
DEFAULT_OUT_DIR = Path("../data/processed")


def parse_score(s: Any) -> int | None:
    """'6: marginally above...' or '3 good' → 6 / 3."""
    if not s:
        return None
    text = str(s).strip()
    if not text:
        return None
    head = text.split(":", 1)[0].split()[0]
    try:
        return int(head)
    except (ValueError, IndexError):
        return None


def unwrap(content: dict[str, Any] | None, field: str) -> Any:
    """v2 wraps content fields as {value: x}; v1 stores them plain."""
    val = (content or {}).get(field)
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


def parse_paper(note: dict[str, Any], venue: str, api_version: str) -> Paper:
    content = note.get("content") or {}
    invitations = note.get("invitations") or []
    is_withdrawn = any("Withdrawn" in (inv or "") for inv in invitations)

    pdf_val = unwrap(content, "pdf")
    pdf_url: str | None = None
    if pdf_val:
        s = str(pdf_val)
        pdf_url = f"https://openreview.net{s}" if s.startswith("/") else s

    return Paper(
        forum_id=note["forum"],
        raw_id=note["id"],
        venue=venue,
        api_version=api_version,
        title=str(unwrap(content, "title") or "").strip(),
        abstract=str(unwrap(content, "abstract") or "").strip(),
        authors=unwrap(content, "authors") or [],
        keywords=unwrap(content, "keywords") or [],
        primary_area=unwrap(content, "primary_area"),
        pdf_url=pdf_url,
        is_withdrawn=is_withdrawn,
    )


def signer_handle(reply: dict[str, Any]) -> str:
    sigs = reply.get("signatures") or []
    return sigs[0].rsplit("/", 1)[-1] if sigs else "?"


def reply_content(reply: dict[str, Any]) -> dict[str, Any]:
    """Return reply content with v2 {value: ...} wrappers stripped."""
    raw = reply.get("content") or {}
    return {
        k: (v.get("value") if isinstance(v, dict) and "value" in v else v)
        for k, v in raw.items()
    }


def join_sections(*pairs: tuple[str, Any]) -> str:
    parts = [f"### {label}\n{val}" for label, val in pairs if val]
    return "\n\n".join(parts)


def parse_review_v2(reply: dict[str, Any], forum_id: str, venue: str) -> Review:
    c = reply_content(reply)
    summary = c.get("summary")
    strengths = c.get("strengths")
    weaknesses = c.get("weaknesses")
    questions = c.get("questions")
    review_text = join_sections(
        ("Summary", summary),
        ("Strengths", strengths),
        ("Weaknesses", weaknesses),
        ("Questions", questions),
    )
    return Review(
        review_id=reply["id"],
        forum_id=forum_id,
        venue=venue,
        api_version="v2",
        reviewer_handle=signer_handle(reply),
        rating=parse_score(c.get("rating")),
        confidence=parse_score(c.get("confidence")),
        summary=summary,
        strengths=strengths,
        weaknesses=weaknesses,
        questions=questions,
        soundness=parse_score(c.get("soundness")),
        presentation=parse_score(c.get("presentation")),
        contribution=parse_score(c.get("contribution")),
        review_text=review_text,
        raw_content=c,
    )


def parse_review_v1(reply: dict[str, Any], forum_id: str, venue: str) -> Review:
    c = reply_content(reply)
    summary = c.get("summary_of_the_paper")
    sw_combined = c.get("strength_and_weaknesses")
    cqn = c.get("clarity,_quality,_novelty_and_reproducibility")
    overall = c.get("summary_of_the_review")
    review_text = join_sections(
        ("Summary", summary),
        ("Strengths and Weaknesses", sw_combined),
        ("Clarity / Quality / Novelty / Reproducibility", cqn),
        ("Overall Verdict", overall),
    )
    return Review(
        review_id=reply["id"],
        forum_id=forum_id,
        venue=venue,
        api_version="v1",
        reviewer_handle=signer_handle(reply),
        rating=parse_score(c.get("recommendation")),
        confidence=parse_score(c.get("confidence")),
        summary=summary,
        overall_verdict=overall,
        correctness=parse_score(c.get("correctness")),
        technical_novelty=parse_score(c.get("technical_novelty_and_significance")),
        empirical_novelty=parse_score(c.get("empirical_novelty_and_significance")),
        review_text=review_text,
        raw_content=c,
    )


def parse_meta(
    forum_id: str,
    replies: list[dict[str, Any]],
    venue: str,
    api_version: str,
) -> MetaReview | None:
    """Build one MetaReview by combining Meta_Review (v2 only) + Decision."""
    meta: dict[str, Any] = {}
    decision: dict[str, Any] = {}
    meta_id = ""

    for r in replies:
        kind = reply_kind(r)
        if kind == "Meta_Review":
            meta = reply_content(r)
            meta_id = r["id"]
        elif kind == "Decision":
            decision = reply_content(r)
            meta_id = meta_id or r["id"]

    if not meta and not decision:
        return None

    if api_version == "v1":
        c = decision or meta
        return MetaReview(
            meta_id=meta_id,
            forum_id=forum_id,
            venue=venue,
            api_version=api_version,
            metareview=c.get("metareview:_summary,_strengths_and_weaknesses")
            or c.get("metareview"),
            decision=c.get("decision"),
            why_not_higher=c.get("justification_for_why_not_higher_score"),
            why_not_lower=c.get("justification_for_why_not_lower_score"),
            raw_content=c,
        )

    return MetaReview(
        meta_id=meta_id,
        forum_id=forum_id,
        venue=venue,
        api_version=api_version,
        metareview=meta.get("metareview"),
        decision=decision.get("decision"),
        why_not_higher=meta.get("justification_for_why_not_higher_score"),
        why_not_lower=meta.get("justification_for_why_not_lower_score"),
        raw_content={**meta, **decision},
    )


def normalize_one_venue(
    venue: str, raw_dir: Path, out_dir: Path
) -> tuple[int, int, int, Counter[str]]:
    if venue not in VENUE_CONFIG:
        raise typer.BadParameter(f"unknown venue '{venue}'")
    api_version, _ = VENUE_CONFIG[venue]

    raw_file = raw_dir / venue / "submissions.jsonl"
    if not raw_file.exists():
        raise FileNotFoundError(f"missing raw file: {raw_file}")

    out = out_dir / venue
    out.mkdir(parents=True, exist_ok=True)
    papers_f = (out / "papers.jsonl").open("w")
    reviews_f = (out / "reviews.jsonl").open("w")
    metas_f = (out / "meta_reviews.jsonl").open("w")

    n_papers = n_reviews = n_metas = 0
    skipped = Counter[str]()

    parse_review = parse_review_v1 if api_version == "v1" else parse_review_v2

    with raw_file.open() as fh:
        for line in fh:
            note = json.loads(line)
            paper = parse_paper(note, venue, api_version)
            papers_f.write(paper.model_dump_json() + "\n")
            n_papers += 1

            replies = (note.get("details") or {}).get("directReplies") or []
            for r in replies:
                kind = reply_kind(r)
                if kind == "Official_Review":
                    try:
                        review = parse_review(r, paper.forum_id, venue)
                    except Exception as e:
                        skipped[f"review:{type(e).__name__}"] += 1
                        continue
                    reviews_f.write(review.model_dump_json() + "\n")
                    n_reviews += 1
                elif kind in {"Meta_Review", "Decision", "Official_Comment", "?"}:
                    pass
                else:
                    skipped[f"unknown_kind:{kind}"] += 1

            meta = parse_meta(paper.forum_id, replies, venue, api_version)
            if meta:
                metas_f.write(meta.model_dump_json() + "\n")
                n_metas += 1

    papers_f.close()
    reviews_f.close()
    metas_f.close()
    return n_papers, n_reviews, n_metas, skipped


@app.command()
def run(
    venue: str = typer.Option(..., help="Venue key"),
    raw_dir: Path = typer.Option(DEFAULT_RAW_DIR),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR),
) -> None:
    """Normalize one venue."""
    n_p, n_r, n_m, skipped = normalize_one_venue(venue, raw_dir, out_dir)
    console.print(f"[green]{venue}[/]  papers={n_p}  reviews={n_r}  meta={n_m}")
    if skipped:
        console.print(f"  skipped: {dict(skipped)}")


@app.command()
def run_all(
    raw_dir: Path = typer.Option(DEFAULT_RAW_DIR),
    out_dir: Path = typer.Option(DEFAULT_OUT_DIR),
) -> None:
    """Normalize every configured venue."""
    grand: list[tuple[str, int, int, int]] = []
    for venue in VENUE_CONFIG:
        console.rule(f"[bold]{venue}[/]")
        n_p, n_r, n_m, skipped = normalize_one_venue(venue, raw_dir, out_dir)
        console.print(f"  papers={n_p}  reviews={n_r}  meta={n_m}")
        if skipped:
            console.print(f"  skipped: {dict(skipped)}")
        grand.append((venue, n_p, n_r, n_m))

    console.rule("[bold]summary[/]")
    console.print(f"  {'venue':<12} {'papers':>8} {'reviews':>8} {'meta':>6}")
    for v, p, r, m in grand:
        console.print(f"  {v:<12} {p:>8} {r:>8} {m:>6}")
    console.print(
        f"  {'TOTAL':<12} {sum(p for _,p,_,_ in grand):>8} "
        f"{sum(r for _,_,r,_ in grand):>8} {sum(m for _,_,_,m in grand):>6}"
    )


if __name__ == "__main__":
    app()
