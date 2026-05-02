# Data Sources

> **Status**: stub. Finalize during W1.

## Primary source: OpenReview

- **API docs**: https://docs.openreview.net/
- **Coverage**: ICLR (all years since 2018), NeurIPS (2022+ partial, 2024 full), and others
- **Format**: JSON metadata + PDF papers + plaintext reviews

## In-scope venues for v1

| Venue | Year | Est. papers | Est. reviews |
|-------|------|-------------|--------------|
| ICLR  | 2023 | ~1,500      | ~6,000       |
| ICLR  | 2024 | ~2,200      | ~9,000       |
| ICLR  | 2025 | ~3,800      | ~16,000      |
| NeurIPS | 2024 | ~4,500    | ~18,000      |
| **Total** | — | **~12,000** | **~49,000** |

(Rough estimates. To be confirmed in W1 ingestion.)

## Out-of-scope for v1

- ICML (separate review process, not on OpenReview consistently)
- CVPR / ACL / EMNLP (not OpenReview-native)
- Workshop tracks (only main conference accepts)
- Pre-2023 ICLR (review format differences)

## Compliance & ethics

- **Reviewer identities**: OpenReview makes some reviewer identities public after acceptance. PaperRadar **does not surface them**. We use anonymous handles ("Reviewer 1", "Area Chair") only.
- **ToS check**: Read OpenReview terms in W1. Confirm bulk download for non-commercial public-facing tool is allowed.
- **Author identities**: Author names are public on accepted papers. We display them as-is.
- **Rate limiting**: Cache aggressively. Single ingestion pass per venue, then incremental.

## Data refresh policy

- **v1**: Static snapshot taken in W1–W2. Not refreshed during the 8-week MVP.
- **Post-launch**: If the project is maintained, plan a quarterly refresh after each major submission cycle.

## Storage layout

```
data/
├── raw/           # original API responses + PDFs (gitignored)
│   ├── openreview/
│   │   ├── iclr-2023/
│   │   ├── iclr-2024/
│   │   ├── iclr-2025/
│   │   └── neurips-2024/
├── processed/     # cleaned text, parsed sections (gitignored)
└── eval/          # ground-truth eval queries + golden answers
    ├── golden_pairs.jsonl
    └── manual_annotations.jsonl
```

## Open data questions

- [ ] PDF parsing fallback strategy when docling fails on a particular paper?
- [ ] How to handle "withdrawn" submissions — include reviews or skip?
- [ ] How to handle rejected papers that have no acceptance signal — do we keep them in the index?
- [ ] Multi-version papers (camera-ready vs original submission) — which one indexes?
