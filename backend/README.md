# PaperRadar Backend

Python RAG pipeline. Managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
cd backend
uv sync                              # install deps + Python 3.12
```

OpenReview credentials are **optional**. Public papers and reviews are
accessible anonymously (verified W1-D1, 2026-05-03). Only set them in
`.env` if you later need restricted content.

## W1 quick checks

```bash
# pull 1 submission, print its structure (validate API)
uv run python -m paperradar.ingest.openreview explore --venue iclr2024

# pull N submissions + replies into data/raw/{venue}/submissions.jsonl
uv run python -m paperradar.ingest.openreview fetch --venue iclr2024 --limit 5
```

Verified output: ICLR 2024 has 7,404 submissions; each one's
`details.directReplies` contains 4 reply types (Official_Review,
Official_Comment, Meta_Review, Decision).

## Layout

```
backend/
├── pyproject.toml
├── .env.example
├── src/paperradar/
│   ├── __init__.py
│   └── ingest/
│       └── openreview.py     # API v2 client + explore/fetch CLI
└── tests/
```
