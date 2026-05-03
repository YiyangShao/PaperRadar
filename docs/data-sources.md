# Data Sources

> **Status**: ingestion verified, normalization pending W2.
> **Last updated**: 2026-05-03

## Primary source: OpenReview

- **API docs**: https://docs.openreview.net/
- **Two API generations in active use**:
  - **v1** (legacy): pre-2024 venues, e.g. ICLR 2023. Plain string content fields.
  - **v2** (current): 2024+ venues. Content fields wrapped as `{"value": ...}`.
- **Authentication**: not required for public papers and reviews. Verified
  anonymous access on 2026-05-03.

## Ingested venues (W1, full snapshot)

| Venue | API | Papers | Replies | Official Reviews | File size |
|-------|-----|-------:|--------:|-----------------:|----------:|
| ICLR 2023    | v1 |  3,792 |  21,299 |  14,335 |  88 MB |
| ICLR 2024    | v2 |  7,404 |  44,782 |  28,028 | 176 MB |
| ICLR 2025    | v2 | 11,672 |  75,621 |  46,748 | 267 MB |
| NeurIPS 2024 | v2 |  4,236 |  25,373 |  16,644 |  93 MB |
| **Total**    | —  | **27,104** | **167,075** | **105,755** | **~624 MB** |

Reply distribution across all venues:

| Kind                     | Count    | Notes |
|--------------------------|---------:|-------|
| Official_Review          | 105,755  | Per-reviewer evaluation (the core data) |
| Meta_Review              |  14,508  | Area Chair summary (only ICLR 2024+) |
| Decision                 |  22,535  | Program Chair final outcome |
| Official_Comment         |  16,912  | Mostly author rebuttals |
| Unclassified (`?`)       |   7,365  | See "Open issues" below |

## Schema differences between v1 and v2

ICLR 2023 (v1) and ICLR 2024+ (v2) reviews use **different field names and a
different reply structure**. Any normalization layer must branch on API version.

### Per-review fields

| Concept            | ICLR 2023 (v1)                                    | ICLR 2024+ (v2)         |
|--------------------|---------------------------------------------------|-------------------------|
| Paper summary      | `summary_of_the_paper`                            | `summary`               |
| Strengths          | `strength_and_weaknesses` (combined)              | `strengths`             |
| Weaknesses         | (combined as above)                               | `weaknesses`            |
| Numeric quality    | `correctness`, `tech_novelty_*`, `empirical_*`    | `soundness`, `presentation`, `contribution` |
| Score              | `recommendation` (1–10)                           | `rating` (1–10)         |
| Reviewer certainty | `confidence`                                      | `confidence`            |
| Open questions     | (in body of `summary_of_the_review`)              | `questions`             |

### Reply structure

- **ICLR 2024+**: `Meta_Review` and `Decision` are separate replies (signed
  by Area Chair vs Program Chairs).
- **ICLR 2023 / NeurIPS 2024**: `Decision` reply contains both decision and
  meta-review fields, signed by Program Chairs. No separate `Meta_Review`.

## Compliance & ethics

- **License**: OpenReview reviews are released under **CC BY 4.0**. We are
  required to provide attribution but may publish derivative works.
- **Reviewer identities**: OpenReview generates anonymized handles
  (`Reviewer_U7B8`, `Area_Chair_hyPi`). We display these handles only;
  we do not attempt to deanonymize.
- **Author identities**: visible on accepted papers; we display them as-is.
- **Rate limiting**: not encountered. Single ingestion pass per venue;
  incremental refresh planned for v2.

## Storage layout

```
data/
├── raw/                            # gitignored
│   ├── iclr2023/submissions.jsonl  # one line = one v1 Note + details.directReplies
│   ├── iclr2024/submissions.jsonl  # v2 schema
│   ├── iclr2025/submissions.jsonl  # v2 schema
│   └── neurips2024/submissions.jsonl  # v2 schema
├── processed/                      # W2: normalized {paper, reviews[]}
└── eval/                           # ground-truth pairs (W3+)
```

## Open issues (queue for W2 normalization)

- [ ] **Unclassified replies (7,365)**: 3,380 in ICLR 2025 and 3,584 in
  NeurIPS 2024. Likely `Senior_Area_Chair_*` or `Confidential_Comment`
  invitations. Investigate sample + decide whether to keep, drop, or
  re-classify.
- [ ] **v1 vs v2 schema bridge**: design a unified internal `Review` model
  that maps both field sets onto the same structure.
- [ ] **Withdrawn submissions**: ICLR includes withdrawn papers in the
  `Submission` invitation. Decision: keep (their reviews are still
  signal), but flag with `is_withdrawn` derived from invitations list.
- [ ] **Multi-version papers**: a paper's `forum` is stable across
  revisions. We currently keep the original Submission record. Decide
  whether to also fetch the camera-ready revision.
- [ ] **PDFs**: not yet downloaded. Each paper has a `content.pdf`
  pointer. W1 Day 3-4 task.
