# PaperRadar — Product Requirements Document

> **Status**: v0.1 (locked for 8-week MVP)
> **Owner**: Lucas
> **Last updated**: 2026-05-02
> **Target launch**: 2026-06-27 (W8 end)

---

## 1. Vision

**Help AI/ML researchers find the most similar prior submissions to their draft, and read what reviewers actually said about them — grounded in real OpenReview data.**

PaperRadar is a retrieval-first RAG system over 12K+ papers and 50K+ peer reviews. It is positioned as a research literacy tool, not a peer-review-gaming tool.

## 2. Problem

ML researchers preparing a submission today have:
- **No way to learn from prior reviews at scale** — OpenReview hosts 36K+ papers and 141K+ reviews, but search is keyword-based and unusable for "find papers similar to mine"
- **No grounded perspective on reviewer concerns** — they guess at what reviewers will object to instead of reading what reviewers historically objected to
- **No tooling to support self-review before submission** — Google PAT generates AI feedback, but it's not grounded in real prior reviews

The pain is highest for **first-time submitters and PhD students**, who have the steepest information asymmetry vs. senior reviewers.

## 3. Target users (priority order)

| Priority | User | Why |
|----------|------|-----|
| **P0** | AI/ML PhD students submitting to ICLR/NeurIPS for the first time | Highest pain, most viral sharing |
| **P1** | Mid-career researchers studying review trends in their subfield | Recurring usage, deep engagement |
| **P2** | AI/ML hiring managers evaluating candidate projects | Hidden audience — they will encounter PaperRadar via Twitter/HN |

P2 is **not** a user we design for, but the project must look credible to them.

## 4. Differentiation

| Existing tool | What it does | What PaperRadar does differently |
|---------------|--------------|----------------------------------|
| OpenReviewer (NAACL 2025) | LLM writes reviews | We **retrieve** historical reviews, no generation of new reviews |
| Google PAT (NeurIPS/ICML pilots) | LLM gives author pre-submission feedback | We ground every observation in real OpenReview text + link |
| Paper Copilot | Archives reviews | We do retrieval + analysis, not just storage |

**Sharpest differentiation**: retrieval-first + a public retrieval-quality benchmark across 5 chunking × 3 retriever × 2 reranker configs. No competitor has published a comparable benchmark.

## 5. Scope

### MVP IN (W1–W8)

**Data** (ingested W1-D2, see `docs/data-sources.md` for breakdown)
- ICLR 2023, 2024, 2025
- NeurIPS 2024
- **27,104 papers, 105,755 official reviews** (verified 2026-05-03)
- All English, all from OpenReview public API
- Note: ICLR 2023 uses API v1 with a different review schema; v1↔v2
  normalization is a W2 task

**Core user-facing features**
1. Paste an abstract OR upload a PDF → get top-10 most similar prior submissions
2. For each match: a grounded summary of what reviewers said, organized by 4 themes (methodology, novelty, experiments, writing)
3. Every claim links back to the original OpenReview review

**Engineering deliverables**
- Hybrid retrieval pipeline (BM25 + dense + reranker)
- Public evaluation harness (RAGAS + custom metrics)
- Ablation report: 5 chunking × 3 retriever × 2 reranker matrix
- Architecture diagram + technical blog post

**Demo assets**
- Landing page (paperradar.dev or similar)
- 30-second demo video / GIF
- 3–5 sample queries pre-loaded
- Public benchmark leaderboard

### MVP OUT (v2 or later)

- CVPR / ACL / EMNLP / other conferences
- Trend visualization over years
- Agent-style multi-step reasoning ("find similar → summarize rejection reasons → suggest revision")
- Authenticated user accounts / saved searches
- API access / commercial tier
- Reviewer identity surfacing (we will *never* expose reviewer names even though OpenReview makes them public)

## 6. Feature priority

| Priority | Feature | Justification |
|----------|---------|---------------|
| P0 | Abstract/PDF → similar papers retrieval | Core value loop |
| P0 | Grounded review summary with citations | Trust, defensibility |
| P0 | Public evaluation report | Recruiting leverage |
| P0 | Landing page + demo video | Distribution prerequisite |
| P1 | Theme-clustered review summary (4 buckets) | UX polish |
| P1 | Reverse links to OpenReview | Academic integrity signal |
| P2 | Simple chat UI ("ask about this paper's reviews") | Demo flair |
| P2 | Confidence scores on retrieval | Power-user feature |

## 7. Tech stack (locked)

| Layer | Choice | Why |
|-------|--------|-----|
| Language | Python 3.12 (backend), TypeScript (frontend) | Standard AI engineering |
| RAG framework | LlamaIndex | Best fit for retrieval-heavy use case |
| PDF parsing | docling (primary), GROBID (fallback) | Don't roll your own |
| Embeddings | OpenAI `text-embedding-3-large` + BGE-M3 (compared) | Eval requires comparison |
| Vector DB | pgvector on Supabase | Hiring-relevant Postgres skill |
| Retrieval | Hybrid: BM25 + dense + Cohere Rerank | Standard battle-tested combo |
| LLM (generation) | Claude Sonnet 4.6 | Best quality |
| LLM (cheap calls) | Claude Haiku 4.5 | Cost control |
| Frontend | Next.js 16 + Vercel | Hiring-relevant |
| Hosting | Vercel + Supabase | Avoid infra rabbit holes |
| Eval | RAGAS + custom harness | Industry standard + customization |

## 8. Success metrics

| Tier | Metric | Target |
|------|--------|--------|
| **L1 must-hit** | Working demo + benchmark report + landing page live | Binary: yes/no by W8 end |
| **L2 expected** | HN front page OR Twitter ≥100 retweets OR GitHub ≥500 stars | Any one |
| **L3 stretch** | Real users during NeurIPS 2026 submission window OR ≥3 recruiter inbounds attributed to project | Any one |

## 9. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PDF parsing eats 40% of project time | High | High | Use docling out-of-the-box, do not optimize |
| Framing read as "game peer review" | Medium | High | Explicit positioning in README + landing page; no reviewer identity exposure |
| Google PAT or OpenReviewer ships overlapping feature | Low | Medium | Differentiation is retrieval-first, not generation — they don't compete directly |
| 8 weeks insufficient | Medium | Medium | MVP is aggressively scoped; weekly checkpoints |
| Evaluation rushed at the end | Medium | **Critical** | Eval harness MUST start by W3 latest |
| Eval ground-truth dataset is messy | Medium | Medium | Sample 200 papers in W1 to validate pipeline early |
| OpenReview API rate limits / ToS issues | Low | High | Read ToS in W1; cache aggressively; respect rate limits |

## 10. Constraints & assumptions

- Solo developer (Lucas)
- ~10–15 hrs/week available
- Total budget: <$300 for OpenAI/Anthropic credits + Supabase/Vercel hosting
- All data sources are public; no proprietary data

## 11. Open questions (resolve by W1 end)

- [ ] Should we register `paperradar.dev` or `paperradar.ai` (or both)?
- [ ] Does OpenReview ToS allow bulk download of reviews for a public-facing tool? (read carefully in W1)
- [ ] Do we redact reviewer numbers (Reviewer 1, Reviewer 2…) entirely or keep them as anonymous handles?
- [ ] Should NeurIPS 2024 be in scope for v1, or is ICLR-only enough? (data volume question)

## 12. Out of scope (explicit non-goals)

- Generating reviews
- Predicting accept/reject probability as the headline feature (we may show it as a secondary signal, but the headline is "find similar reviews")
- Replacing the peer review process or human reviewers
- Surfacing reviewer identities even when public
- Building a commercial product (this is a portfolio + research literacy tool)
