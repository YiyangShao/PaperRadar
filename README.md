# PaperRadar

> **Find the papers most similar to yours, and read what reviewers actually said about them.**

PaperRadar is a retrieval-first RAG system over 12K+ AI/ML papers and 50K+ peer reviews from OpenReview (ICLR 2023–2025, NeurIPS 2024). Given a paper draft or abstract, it surfaces the most similar prior submissions and grounds every observation in the original review text.

Built as a research literacy tool — not a tool to game peer review.

---

## Status

🚧 In active development. MVP target: 8 weeks (W1 = 2026-W19, W8 = 2026-W26).

See [PRD.md](./PRD.md) for product spec and [ROADMAP.md](./ROADMAP.md) for week-by-week milestones.

## Project layout

```
RAG/
├── README.md          # this file
├── PRD.md             # product requirements + scope
├── ROADMAP.md         # 8-week milestone plan
├── docs/              # architecture, evaluation, data sources
├── backend/           # Python RAG pipeline (LlamaIndex + pgvector)
├── frontend/          # Next.js landing + demo UI
├── data/              # raw / processed / eval data (gitignored)
├── scripts/           # one-shot scripts
└── notebooks/         # experiments and ablations
```

## Tech stack (locked)

- **Language**: Python 3.12 (backend), TypeScript (frontend)
- **RAG framework**: LlamaIndex
- **PDF parsing**: docling (primary), GROBID (fallback)
- **Embeddings**: OpenAI `text-embedding-3-large` + BGE-M3 (compared)
- **Vector DB**: pgvector on Supabase Postgres
- **Retrieval**: Hybrid (BM25 + dense) + Cohere Rerank
- **LLMs**: Claude Sonnet 4.6 (generation), Haiku 4.5 (cheap calls)
- **Frontend**: Next.js 16 + Vercel
- **Eval**: RAGAS + custom harness

## Non-goals (v1)

- Generating reviews on behalf of reviewers
- Predicting accept/reject as a primary feature
- Multi-conference expansion beyond ICLR + NeurIPS
- Authenticated user accounts
