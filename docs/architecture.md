# Architecture

> **Status**: stub. Fill in during W2 once the data pipeline is real.

## High-level data flow

```
OpenReview API ──► ingest/ ──► raw JSON + PDFs ──► parse/ (docling)
                                                       │
                                                       ▼
                                                  clean text + metadata
                                                       │
                                                       ▼
                                              chunk/ ──► embed/ ──► pgvector (Supabase)
                                                                          │
                                                                          ▼
User query ──► API (FastAPI) ──► retrieve/ (BM25 + dense + rerank) ──► generate/ (Claude) ──► response
                                                                          │
                                                                          ▼
                                                                       eval/ harness
```

## Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| Ingest | `backend/src/paperradar/ingest/` | Pull papers + reviews from OpenReview API, store raw |
| Parse | `backend/src/paperradar/parse/` | PDF → clean text + section metadata via docling |
| Index | `backend/src/paperradar/index/` | Chunking + embedding + write to pgvector |
| Retrieve | `backend/src/paperradar/retrieve/` | BM25 + dense + RRF + Cohere Rerank |
| Generate | `backend/src/paperradar/generate/` | Theme classification + grounded summary via Claude |
| Eval | `backend/src/paperradar/eval/` | Retrieval metrics + RAGAS faithfulness |
| API | `backend/src/paperradar/api/` | FastAPI endpoints |
| Frontend | `frontend/` | Next.js 16 search UI + landing |

## Data model (Postgres)

To be defined in W1. Sketch:

```
papers       (paper_id, venue, year, title, abstract, authors, openreview_url)
reviews      (review_id, paper_id, role, text, rating, confidence)
chunks       (chunk_id, source_id, source_type, text, embedding vector(3072))
ingestion_runs (run_id, started_at, status, n_papers, n_reviews)
```

## Open architectural questions

- [ ] Single vs separate embedding namespaces for paper text vs reviews?
- [ ] Store full reviews as one chunk or sentence-windowed chunks?
- [ ] Where to do reranking — DB-side or app-side?
- [ ] Whisper-style streaming for the generation endpoint, or batch?
