# Evaluation Methodology

> **Status**: stub. This becomes the primary recruiting artifact in W5–W7.
>
> If this document is half-finished by W8, the project's recruiting value drops by ~50%. Treat it as a P0 deliverable.

## Why this exists

99% of RAG portfolio projects say "I built a RAG." 1% say "I built a RAG and rigorously evaluated it." The 1% gets interviews.

This document is where PaperRadar publishes its evaluation methodology, results, and ablation matrix.

## Evaluation tiers

### Tier 1 — Retrieval quality

**Question**: Given a paper, can we find papers with similar reviewer concerns?

| Metric | What it measures |
|--------|------------------|
| `retrieval@5` / `retrieval@10` | Hit rate of "true similar" papers in top-K |
| MRR (Mean Reciprocal Rank) | Where in the top-K does the first hit land |
| NDCG@10 | Graded relevance ranking quality |
| Latency p50/p95 | User-facing responsiveness |
| $/query | Cost per retrieval |

**Ground truth**: 50 hand-curated paper pairs in W3, expanded to 200 by W5. Sources of "true similar":
- Same authors across years
- Cross-citations within OpenReview
- Same workshop / track
- Manual annotation

### Tier 2 — Generation faithfulness

**Question**: Are the generated review summaries actually supported by the source reviews?

| Metric | Tool |
|--------|------|
| Faithfulness | RAGAS |
| Answer relevance | RAGAS |
| Context precision | RAGAS |
| Hallucination rate (manual) | 30-sample manual audit |

**Pass bar**: ≥95% of claims in summaries must link to source review text.

### Tier 3 — End-to-end usefulness (qualitative)

10 ML researchers (recruited via Twitter) try PaperRadar with their own draft and answer:

- Did the top results feel "actually similar"?
- Did the review summary surface things you hadn't thought about?
- Would you use this again before your next submission?

Not a metric, but a forcing function for quality.

## Ablation matrix (W5)

5 chunking × 3 retrieval × 2 reranker = **30 configurations**.

### Chunking strategies

1. Fixed 256 tokens
2. Fixed 512 tokens
3. Sentence-window (3-sentence)
4. Section-aware (use paper section structure)
5. Recursive (LlamaIndex default)

### Retrievers

1. BM25 only
2. Dense only (`text-embedding-3-large`)
3. Hybrid (BM25 + dense via RRF)

### Rerankers

1. None
2. Cohere Rerank v3

### What gets reported

For each of the 30 configs:
- retrieval@10
- MRR
- Latency p50
- $/query

**Output**: a single CSV + a Pareto-frontier chart in `docs/evaluation.md`. The Pareto chart is the recruiting hook.

## Reproducibility

- All eval scripts in `backend/src/paperradar/eval/`
- All eval data (queries + golden answers) in `data/eval/` with a public download link
- All raw run results committed to `eval/results/` as CSV

A reader should be able to clone the repo, run `make eval`, and reproduce every number in the report within ±2%.

## What this document looks like by W8

By the end of the project, this file should contain:

1. Methodology (this section, polished)
2. Final ablation matrix table
3. Pareto frontier chart
4. Top-3 surprises ("what we expected vs what happened")
5. Reproduction instructions
6. Limitations
