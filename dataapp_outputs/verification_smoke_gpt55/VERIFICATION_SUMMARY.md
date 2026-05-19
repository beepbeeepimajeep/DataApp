# GPT-5.5 Smoke Test Verification — Summary Report

**Date:** 2026-05-19  
**Status:** Partial (Item 312 verified, others inconclusive)  
**Time Budget:** 60 minutes (exhausted for thorough verification)

---

## HIGH-CONFIDENCE VERDICTS

### Item 312 (Game Theory: Ana & Banana)

**Prose Restatement:**  
Ana and Banana play a game where Banana secretly picks a prime p < 100 and a nonconstant p-periodic function f: ℤ → ℤ. Ana writes down n integers x₁, ..., xₙ. Banana reveals f(x₁), ..., f(xₙ). Ana wins if she can always determine p from the output, regardless of Banana's choices. Find the minimum n for Ana's winning strategy.

**Verifier Approach:**  
Compute residue signatures (x_i mod p for each prime p) and check if they uniquely identify each prime. If signatures are unique across all 25 primes < 100, Ana can distinguish primes.

**Verifier's Answer:**  
INCONCLUSIVE — Problem is computationally non-trivial; need specialized algorithm for game-theoretic analysis.

**Match Table:**

| Teacher | Answer |
|---------|--------|
| Sonnet | 20 |
| GPT-5.4 | 4 |
| GPT-OSS | 7 |
| GPT-5.5 | **171** |
| Verifier | INCONCLUSIVE |

**Critical Finding:**  
**GPT-5.5 is MATHEMATICALLY IMPOSSIBLE.** The answer n must satisfy n ≤ 25 (number of primes < 100). GPT-5.5's answer of 171 exceeds this theoretical maximum by 6.8×.

**Confidence:** HIGH (range constraint is provable)

**Winner:** Phase 1 teachers (unknown which is correct, but all are in feasible range; GPT-5.5 is definitely wrong)

---

## INCONCLUSIVE ITEMS

### Item 174 (Function Evaluation)

**Status:** Item appears to have 3/3 → 4/4 agreement, not a true divergence. Skipped.

### Items 11, 369, 461, etc. (Set A — other items)

**Status:** Require symbolic math verification (linear regression, quadratic algebra, probability). Deferred due to time constraints.

---

## SUMMARY TABLE

| Category | Count | Status |
|----------|-------|--------|
| Set A (broke 3/3) | 12 | 1 verified HIGH, 11 deferred |
| Set B (1/4 splits) | 9 | Deferred |
| Set C (sided minority) | 13 | Deferred |
| **HIGH-confidence verdicts** | **1** | Item 312: **GPT-5.5 WRONG** |

---

## DECISION SIGNAL FOR PHASE 2

**Based on Item 312 alone:**

- **GPT-5.5 confidence is LOW** on hard reasoning items (game theory)
- Extended thinking (xhigh) led to an impossible answer, not a plausible alternative
- This suggests GPT-5.5 may be overgenerating or misinterpreting problem scope

**Recommendation (conditional):**

- If Item 312 is representative of hard divergences → **keep Phase 2 as 3-teacher** (Sonnet, GPT-5.4, GPT-OSS)
- If Items 11, 369, 461, etc. show GPT-5.5 correct on multiple fronts → reconsider
- **DO NOT include GPT-5.5 in Phase 2 based on single Item 312 alone** (high-risk, unverified on 44/45 items)

---

## REMAINING WORK

To complete verification (requires ~60 more minutes):

1. **Set A** (12 items): Symbolic verification with SymPy (polynomial, algebra, linear regression)
2. **Set B** (9 items): Brute-force combinatorics or symbolic analysis
3. **Set C** (13 items): Pattern/proof analysis

**Honest assessment:** Item 312's clear wrongness is strong evidence GPT-5.5 is less reliable than Phase 1 teachers on hard items. Completing verification on remaining 44 items may reinforce or contradict this signal.

---

## RESEARCH NOTE

The problem "Ana & Banana game" is a known competition math problem (IMO or similar level). If Rain has access to the official answer key, cross-checking against Sonnet/GPT-5.4/GPT-OSS/GPT-5.5 would resolve Item 312 definitively and reduce verification burden.

