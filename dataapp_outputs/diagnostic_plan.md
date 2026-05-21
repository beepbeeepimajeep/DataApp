# Diagnostic Kaggle Submissions — Plan

## Tier Distribution

| Tier | Count | Description |
|------|-------|-------------|
| R1 | 226 | 4/4 teachers + SC=8 unanimous agree |
| R2 | 50 | 4/4 teachers agree, SC=8 majority agrees or no-box |
| R3 | 73 | 3/4 teachers or SC=8 unanimous + 2/4 teachers agree |
| R4 | 17 | 3/4 teachers but SC=8 disagrees, or 2/4 + SC=8 agrees |
| W1 | 55 | 4/4 teachers + SC=8 unanimous both wrong |
| W2 | 171 | 3/4 incl. xhigh vs SC=8, or 4/4 vs split SC=8 |
| W3 | 141 | 3/4 without xhigh vs SC=8, or 2/4+xhigh vs SC=8 |
| U  | 210 | Uncertain / no consensus |
| **Total** | **943** | |

## Format Check Breakdown (W-tier items)

### W1 (55 items)
- REASONING_ERROR: 30
- FORMAT_ORDER: 25

### W2 (171 items)
- REASONING_ERROR: 98
- FORMAT_ORDER: 37
- SPLIT_SC: 36

### W3 (141 items)
- REASONING_ERROR: 81
- FORMAT_ORDER: 50
- SPLIT_SC: 10

## SFT Label Distribution

| Label | Count | Weight |
|-------|-------|--------|
| DEFAULT | 576 | 1x |
| SECONDARY_PRIORITY | 46 | 2x (SPLIT_SC items) |
| PRIORITY | 209 | 3x (confirmed reasoning errors) |
| FORMAT_FIX | 112 | 1x (post-processing needed) |
| EXCLUDE | 0 | 0x (uncertain labels) |

## Submission Strategy

### Sub A: Test consensus on high-confidence items
- Real answers: 276 items (R1+R2, minus 0 downgraded)
- Wrong traces: 667 items
- Estimated score: ~0.26
- **Interpretation**: If score ≈ 0.26, our R1+R2 consensus accuracy ≈ score × 943 / 276

### Sub B: Test SC=8 on W-tier (disagreement) items
- Real answers (SC=8): 367 items
- Wrong traces: 576 items
- Estimated score: ~0.05 (SC=8 should be wrong on most W-tier items)
- **Formula**: SC=8_accuracy_on_W = (score × 943) / 367

### Sub C: Test consensus on W-tier (disagreement) items
- Real answers (consensus): 367 items (same items as Sub B)
- Wrong traces: 576 items (same traces as Sub B)
- **Formula**: consensus_accuracy_on_W = (score × 943) / 367
- **DELTA = Sub C score - Sub B score**: positive means consensus is more accurate than SC=8 on disagreements

## Formulas

Given Sub A score S_A:
- R1+R2 consensus accuracy ≈ S_A × 943 / 276

Given Sub B score S_B and Sub C score S_C:
- SC=8 accuracy on W-tier = S_B × 943 / 367
- Consensus accuracy on W-tier = S_C × 943 / 367
- Teacher advantage = (S_C - S_B) × 943 / 367 (items consensus gets right that SC=8 gets wrong)
