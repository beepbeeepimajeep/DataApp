# Diagnostic Kaggle Submissions — Plan

## Tier Distribution

| Tier | Count | Description |
|------|-------|-------------|
| R1 | 294 | 4/4 teachers + SC=8 unanimous agree |
| R2 | 100 | 4/4 teachers agree, SC=8 majority agrees or no-box |
| R3 | 111 | 3/4 teachers or SC=8 unanimous + 2/4 teachers agree |
| R4 | 21 | 3/4 teachers but SC=8 disagrees, or 2/4 + SC=8 agrees |
| W1 | 27 | 4/4 teachers + SC=8 unanimous both wrong |
| W2 | 159 | 3/4 incl. xhigh vs SC=8, or 4/4 vs split SC=8 |
| W3 | 68 | 3/4 without xhigh vs SC=8, or 2/4+xhigh vs SC=8 |
| U  | 163 | Uncertain / no consensus |
| **Total** | **943** | |

## Format Check Breakdown (W-tier items)

### W1 (27 items)
- REASONING_ERROR: 27

### W2 (159 items)
- REASONING_ERROR: 96
- SPLIT_SC: 63

### W3 (68 items)
- REASONING_ERROR: 56
- SPLIT_SC: 12

## SFT Label Distribution

| Label | Count | Weight |
|-------|-------|--------|
| DEFAULT | 689 | 1x |
| SECONDARY_PRIORITY | 75 | 2x (SPLIT_SC items) |
| PRIORITY | 179 | 3x (confirmed reasoning errors) |
| FORMAT_FIX | 0 | 1x (post-processing needed) |
| EXCLUDE | 0 | 0x (uncertain labels) |

## Submission Strategy

### Sub A: Test consensus on high-confidence items
- Real answers: 394 items (R1+R2, minus 0 downgraded)
- Wrong traces: 549 items
- Estimated score: ~0.38
- **Interpretation**: If score ≈ 0.38, our R1+R2 consensus accuracy ≈ score × 943 / 394

### Sub B: Test SC=8 on W-tier (disagreement) items
- Real answers (SC=8): 254 items
- Wrong traces: 689 items
- Estimated score: ~0.05 (SC=8 should be wrong on most W-tier items)
- **Formula**: SC=8_accuracy_on_W = (score × 943) / 254

### Sub C: Test consensus on W-tier (disagreement) items
- Real answers (consensus): 254 items (same items as Sub B)
- Wrong traces: 689 items (same traces as Sub B)
- **Formula**: consensus_accuracy_on_W = (score × 943) / 254
- **DELTA = Sub C score - Sub B score**: positive means consensus is more accurate than SC=8 on disagreements

## Formulas

Given Sub A score S_A:
- R1+R2 consensus accuracy ≈ S_A × 943 / 394

Given Sub B score S_B and Sub C score S_C:
- SC=8 accuracy on W-tier = S_B × 943 / 254
- Consensus accuracy on W-tier = S_C × 943 / 254
- Teacher advantage = (S_C - S_B) × 943 / 254 (items consensus gets right that SC=8 gets wrong)
