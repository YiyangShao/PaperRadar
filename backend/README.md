# PaperRadar Backend

Python RAG pipeline. Managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
cd backend
uv sync                         # install deps
cp .env.example .env            # add OpenReview credentials
```

## W1-D1 quick check

After credentials are in `.env`:

```bash
# pull 1 submission and pretty-print its structure (validate API access)
uv run python -m paperradar.ingest.openreview explore --venue iclr2024

# pull 5 submissions + their direct replies (reviews) to data/raw/iclr2024/
uv run python -m paperradar.ingest.openreview fetch --venue iclr2024 --limit 5
```

## Layout

```
backend/
├── pyproject.toml
├── .env.example
├── src/paperradar/
│   ├── __init__.py
│   └── ingest/             # W1: OpenReview API → raw JSON
│       └── openreview.py
└── tests/
```
