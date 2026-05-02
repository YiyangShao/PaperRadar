# PaperRadar — 8-Week Roadmap

> **Start**: 2026-05-04 (W1 Mon)
> **Launch**: 2026-06-27 (W8 Sat)
> **Effort budget**: ~10–15 hrs/week
>
> A weekly checkpoint exists at the end of each Sunday. If a week's "must-ship" item slips, scope is cut from later weeks — never from evaluation (W3, W5, W7).

---

## W1 — 2026-05-04 → 2026-05-10 — Data foundation

**Goal**: Validate the data pipeline on 100 papers before scaling.

| Day | Task |
|-----|------|
| Mon | Read OpenReview API docs + ToS; confirm bulk download is allowed |
| Mon | Domain decision: register `paperradar.dev` |
| Tue–Wed | Ingest 100 ICLR 2024 papers + reviews via OpenReview API |
| Wed–Thu | PDF parsing pipeline with docling; benchmark on 100 PDFs |
| Fri | Manual sample 20 papers — verify parsed text + reviews are usable |
| Sat | Set up Supabase + pgvector locally; create schema |
| Sun | **Checkpoint**: data pipeline works end-to-end on 100 samples |

**Must-ship**: Repeatable script that ingests N papers from OpenReview, parses PDFs, and lands clean records in Postgres. Schema: `papers`, `reviews`, `chunks` tables.

## W2 — 2026-05-11 → 2026-05-17 — Full indexing + dense baseline

**Goal**: Get a working v0 retrieval baseline on the full corpus.

| Day | Task |
|-----|------|
| Mon–Tue | Scale ingestion to ICLR 2023, 2024, 2025 + NeurIPS 2024 |
| Wed | Chunking strategy v0 (sentence-window + 512 tokens) |
| Thu | Embedding pass with `text-embedding-3-large`; index in pgvector |
| Fri | Build basic retrieval API (FastAPI) — paper → top-10 similar |
| Sat | First eyeball test: pick 5 well-known papers, verify top-10 makes sense |
| Sun | **Checkpoint**: full corpus indexed, dense retrieval baseline works |

**Must-ship**: A queryable index over the entire corpus. Latency not yet optimized.

## W3 — 2026-05-18 → 2026-05-24 — Hybrid + reranker + first eval

**Goal**: Beat the dense baseline + start evaluation now (not later).

| Day | Task |
|-----|------|
| Mon | Add BM25 layer; combine with dense via RRF |
| Tue | Integrate Cohere Rerank as final stage |
| Wed | Build evaluation ground-truth set: 50 papers with known "similar" papers (same authors, same venue track, citation links) |
| Thu | Implement retrieval@5/10, MRR, NDCG metrics |
| Fri | Run baseline + hybrid + reranker on eval set; record results |
| Sat | Investigate retrieval failures qualitatively (10 samples) |
| Sun | **Checkpoint**: first evaluation report committed to repo |

**Must-ship**: A `eval/retrieval_v1.md` report with hard numbers comparing 3 retrieval configs.

## W4 — 2026-05-25 → 2026-05-31 — Review summarization + grounding

**Goal**: Generate trustworthy, grounded review summaries.

| Day | Task |
|-----|------|
| Mon–Tue | Theme classification (methodology / novelty / experiments / writing) on review sentences |
| Wed | Per-theme summarization with Claude Sonnet 4.6, mandatory citation links |
| Thu | Faithfulness evaluation harness (RAGAS) |
| Fri | Tune prompts; reduce hallucination rate |
| Sat | Manual review of 30 generated summaries; flag failure modes |
| Sun | **Checkpoint**: `eval/generation_v1.md` with faithfulness score |

**Must-ship**: Generation step that produces 4-theme summaries with ≥95% claims linkable to source review text.

## W5 — 2026-06-01 → 2026-06-07 — Ablation matrix

**Goal**: The single highest-leverage week for recruiting credibility.

| Day | Task |
|-----|------|
| Mon | Define matrix: 5 chunking × 3 retriever × 2 reranker = 30 configs |
| Tue–Wed | Automate the sweep; estimate cost (<$100) |
| Thu–Fri | Run the full sweep; collect retrieval@10, MRR, latency, $/query |
| Sat | Build a results table + 2 charts (Pareto frontier, retriever vs chunking heatmap) |
| Sun | **Checkpoint**: ablation report drafted in `docs/evaluation.md` |

**Must-ship**: Public ablation report that any engineer can read and reproduce.

## W6 — 2026-06-08 → 2026-06-14 — Frontend + UX

**Goal**: A demo a recruiter or researcher can use in 30 seconds.

| Day | Task |
|-----|------|
| Mon | Next.js 16 scaffold; deploy to Vercel |
| Tue–Wed | Search UI: paste abstract → results list with citations |
| Thu | Per-paper detail view: 4-theme summary + OpenReview links |
| Fri | Landing page: hero, value prop, 3 sample queries, demo video embed |
| Sat | 3–5 hand-curated sample queries with golden results |
| Sun | **Checkpoint**: paperradar.dev live and shareable |

**Must-ship**: Deployed site with working search and 3 prepared sample queries.

## W7 — 2026-06-15 → 2026-06-21 — Blog + benchmark + buffer

**Goal**: Build the launch artifacts. Reserve 2 days for buffer.

| Day | Task |
|-----|------|
| Mon–Tue | Technical blog draft (≥1500 words): how I built it, what worked, what didn't |
| Wed | Architecture diagram (Excalidraw or similar) |
| Thu | Benchmark report: clean tables, charts, methodology |
| Fri | Record 30s demo video; create Twitter thread template |
| Sat–Sun | **Buffer** for whatever broke |

**Must-ship**: Blog post + benchmark report + demo video, all publishable.

## W8 — 2026-06-22 → 2026-06-27 — Launch

**Goal**: Public release with coordinated distribution.

| Day | Task |
|-----|------|
| Mon | Final QA pass; check all links, demo paths, sample queries |
| Tue | Soft launch: post to Twitter, tag 2–3 ML accounts |
| Wed | **Show HN** post (Tuesday/Wednesday morning best for HN) |
| Thu | Reddit r/MachineLearning [Project] post |
| Fri | LinkedIn long-form article |
| Sat | DM 3–5 hiring managers at target companies; update resume + LinkedIn |
| Sun | Retrospective; capture metrics; plan v2 (or sunset) |

**Must-ship**: Project publicly launched with metrics tracked.

---

## Slip rules

If a week falls behind:

1. **Never cut**: W3 eval, W5 ablation, W7 blog. These are the recruiting leverage.
2. **Cut first**: P2 features (chat UI, confidence scores), the 4th theme of summary, NeurIPS 2024 (drop to ICLR-only).
3. **Last resort**: extend timeline to W9–W10. But each extra week is a week of motivation lost — strong default is "cut scope, hold timeline."

## Weekly ritual

Every Sunday 30 min:

- Did this week ship its "must-ship"? Yes/no.
- What evidence is in the repo? (commit, doc, blog draft)
- What's the single biggest risk to next week?
- One scope change candidate?
