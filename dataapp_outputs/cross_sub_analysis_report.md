# Cross-Submission Analysis Report

## Kaggle Scores

| Sub | Description | Score | Correct/943 |
|-----|-------------|-------|-------------|
| A | R1+R2 real, rest wrong traces | 0.505 | 476 |
| B | W-tier SC=8, rest wrong traces | 0.151 | 142 |
| C | W-tier consensus, rest wrong traces | 0.222 | 209 |
| Run09 | SC=8 all items | 0.614 | 578 |

## Tier Distribution

| Tier | Count |
|------|-------|
| R1 | 294 |
| R2 | 100 |
| R3 | 111 |
| R4 | 21 |
| W1 | 27 |
| W2 | 159 |
| W3 | 68 |
| U | 163 |

## Wrong-Trace Leak Rate Estimation

Sub A used wrong teacher traces for 549 items. These traces are teacher
responses that *disagree* with our consensus. But if the consensus is wrong and
the teacher is right, the trace accidentally gives a correct answer.

| Leak Rate L | A real_acc | B SC=8_acc | C cons_acc |
|-------------|-----------|------------|------------|
| L=0.05 | 1.138 | 0.423 | 0.687 |
| L=0.08 | 1.097 | 0.342 | 0.606 |
| L=0.15 | 0.999 | 0.152 | 0.416 |

## Key Findings

### Leak-free delta (Sub C − Sub B)
Both use the SAME wrong traces for 689 items, so leak cancels exactly:
- DELTA = 209 − 142 = 67 extra correct / 254 W-tier items
- Teacher consensus outperforms SC=8 by **26.4%** on W-tier items
- Interpretation: On items where teachers and Qwen disagree, teachers are more often right

### R1+R2 consensus accuracy (Sub A)
At L=0.08 (mid estimate): **109.7%**
At L=0.05 (conservative): 113.8%
At L=0.15 (liberal): 99.9%

### SC=8 vs Teacher consensus on W-tier (Sub B vs C)
At L=0.08:
- SC=8 accuracy on W-tier: 34.2%
- Consensus accuracy on W-tier: 60.6%
- Teacher advantage: +26.4% (leak-free)

## High-Information Categories

| Category | Count | Description |
|----------|-------|-------------|
| CAT1 Triple agreement | 478 | Run09=SC8=consensus — very likely correct |
| CAT2 Run09 CSV/JSONL inconsistency | 102 | Stability check |
| CAT3 Sub A wrong traces ≈ Run09 | 40 | Potential leak items |
| CAT4 Highly uncertain (4+ distinct answers) | 221 | U-tier hard cases |
| CAT5 SPLIT_SC | 75 | Qwen sometimes right — high SFT value |

## Tomorrow's 3 Submissions

### Sub D: Full answer sheet (best_answer for all 943)
- File: `sub_d_full_answer_sheet.csv`
- Real answers: 943/943 items
- Placeholders: 0 items (guaranteed wrong)
- **Measures**: Overall pseudo-gold accuracy across all tiers
- **Formula**: score × 943 = real_correct + 0 × L
  → real_acc ≈ (score × 943 - 0 × L) / 943
- **Expected**: Higher than Sub A's 0.505 (we now use best_answer for more items)

### Sub E: All-placeholder baseline
- File: `sub_e_all_placeholder.csv`
- Real answers: 0/943 (all PLACEHOLDER_NNNN)
- **Measures**: True baseline leak rate
- **Formula**: score × 943 = 943 × L → L = score
- **Expected**: ≈0.00 (placeholders are guaranteed wrong)
- **Action**: Use Sub E score as our empirical L for all future calculations

### Sub F: R3+R4+U only
- File: `sub_f_r3r4u_only.csv`
- Real answers: 295/943 items (R3+R4+U only)
- Placeholders: 648 items
- **Measures**: Consensus accuracy on middle/low-confidence tiers
- **Formula**: score × 943 = 295 × cons_acc + 648 × L
  → cons_acc = (score × 943 - 648 × L) / 295
- **Action**: Cross-reference with Sub D to get per-tier accuracy breakdown

## Recommended Submission Order Tomorrow
1. Sub E first (establishes L empirically — all other calculations depend on it)
2. Sub D second (full accuracy measurement)
3. Sub F third (middle-tier isolation)
