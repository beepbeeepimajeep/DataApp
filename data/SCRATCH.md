## 2026-05-30 Raw teacher responses rescue + compact extraction

### Raw dirs landed
| Teacher | Path | Files | Size |
|---------|------|-------|------|
| xhigh (GPT-5.5) | dataapp_outputs/gpt55_full/ | 943 md files | 7.9 MB |
| sonnet (Claude Sonnet 4.6) | dataapp_outputs/item_XXXX/sonnet_response.md | 943 files | ~70 MB (per-item dirs) |
| gpt4 (GPT-5.4) | dataapp_outputs/item_XXXX/gpt5_4_response.md | 943 files | (same per-item dirs) |
| oss (api-gpt-oss-120b) | dataapp_outputs/item_XXXX/gpt_oss_response.md | 943 files | (same per-item dirs) |
| xhigh reruns | dataapp_outputs/gpt55_rerun_refusals/ | 29 files | 255 KB |

- Total dataapp_outputs: ~82 MB
- Largest single file: 44 KB (item_0093/sonnet_response.md)
- All plain git (no LFS needed — no file >100 MB)
- Note: per-item dirs were gitignored (dataapp_outputs/item_*/); added with `git add -f`

### teacher_answers_compact.json extraction (data/teacher_answers_compact.json)
- Total items: 943, keys "0".."942" (unpadded)
- Items with all 4 keys filled: 940
- xhigh histogram: ok=929, recovered=11 (from xhigh_refusal_recovery.json), excluded=3, no_box=0
- Excluded xhigh items: 68 (free-form multi-numeric wrong answer), 112 (token cap no boxed), 259 (still refused)
- Extraction script: scripts/build_teacher_answers_compact.py
- Spot-checks passed for items 0, 1, 100, 500, 942 (all 4 keys match raw files)

---

## 2026-05-29 xhigh teacher export

- Output: `data/teacher_xhigh_answers.csv`
- Row count: 943
- Status histogram: ok=932, recovered=11, refusal=0, no_box=0
- Failed extraction files: none