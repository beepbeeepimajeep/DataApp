#!/usr/bin/env python3
"""
Audit consensus_normalizer.py for false-disagreement patterns.

Read-only: identifies items at 1/3 or 2/3 that may be false disagreements
due to formatting differences answers_match doesn't handle.

Tests 5 candidate normalizations:
  (a) String equality after whitespace collapse
  (b) Numerical extraction of (a, b) coordinate pairs with 0.01 tolerance
  (c) Same as (b) but also handle [a, b] brackets
  (d) Common LaTeX normalizations
  (e) Strip backslash-escape variants
"""

import json
import re
from pathlib import Path
from collections import Counter
from src.consensus_normalizer import normalize_for_consensus, answers_match


def load_manifest():
    """Load manifest entries."""
    manifest_path = Path("dataapp_outputs/dataset_manifest.jsonl")
    entries = []
    with open(manifest_path) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))
    return entries


def candidate_a_whitespace_collapse(a: str, b: str) -> bool:
    """(a) String equality after whitespace collapse."""
    def normalize(s):
        return re.sub(r'\s+', '', s)
    return normalize(a) == normalize(b)


def candidate_b_coordinate_pairs_parens(a: str, b: str, tol: float = 0.01) -> bool:
    """(b) Extract (a, b) coordinate pairs and compare numerically."""
    def extract_coords(s):
        s = s.strip()
        m = re.match(r'^\(([^,]+),([^)]+)\)$', s)
        if m:
            try:
                x = float(m.group(1).strip())
                y = float(m.group(2).strip())
                return (x, y)
            except ValueError:
                pass
        return None

    ca = extract_coords(a)
    cb = extract_coords(b)

    if ca and cb:
        xa, ya = ca
        xb, yb = cb
        # Relative tolerance for both components
        def within_tol(v1, v2):
            if v2 == 0:
                return abs(v1) < tol
            rel_err = abs(v1 - v2) / max(abs(v1), abs(v2), 1e-10)
            return rel_err < tol
        return within_tol(xa, xb) and within_tol(ya, yb)

    return False


def candidate_c_coordinate_pairs_brackets(a: str, b: str, tol: float = 0.01) -> bool:
    """(c) Extract (a, b) or [a, b] coordinate pairs and compare numerically."""
    def extract_coords(s):
        s = s.strip()
        # Try parentheses
        m = re.match(r'^\(([^,]+),([^)]+)\)$', s)
        if m:
            try:
                x = float(m.group(1).strip())
                y = float(m.group(2).strip())
                return (x, y)
            except ValueError:
                pass
        # Try brackets
        m = re.match(r'^\[([^,]+),([^\]]+)\]$', s)
        if m:
            try:
                x = float(m.group(1).strip())
                y = float(m.group(2).strip())
                return (x, y)
            except ValueError:
                pass
        return None

    ca = extract_coords(a)
    cb = extract_coords(b)

    if ca and cb:
        xa, ya = ca
        xb, yb = cb

        def within_tol(v1, v2):
            if v2 == 0:
                return abs(v1) < tol
            rel_err = abs(v1 - v2) / max(abs(v1), abs(v2), 1e-10)
            return rel_err < tol

        return within_tol(xa, xb) and within_tol(ya, yb)

    return False


def candidate_d_latex_normalizations(a: str, b: str) -> bool:
    """(d) Common LaTeX normalizations: \frac ↔ /, \infty ↔ inf, etc."""
    def normalize_latex(s):
        s = s.strip()
        # \frac{a}{b} → a/b
        s = re.sub(
            r'\\frac\s*\{\s*([^}]+)\s*\}\s*\{\s*([^}]+)\s*\}',
            r'\1/\2',
            s
        )
        # \infty variants
        s = re.sub(r'\\infty', 'inf', s, flags=re.IGNORECASE)
        # Remove \displaystyle, \text{}, \mathrm{}
        s = re.sub(r'\\displaystyle', '', s)
        s = re.sub(r'\\text\s*\{\s*([^}]*)\s*\}', r'\1', s)
        s = re.sub(r'\\mathrm\s*\{\s*([^}]*)\s*\}', r'\1', s)
        # Collapse whitespace
        s = re.sub(r'\s+', '', s)
        return s

    na = normalize_latex(a)
    nb = normalize_latex(b)
    return na == nb


def candidate_e_backslash_escapes(a: str, b: str) -> bool:
    """(e) Strip backslash-escape variants: \38{,}800 ↔ \38,800."""
    def normalize_escapes(s):
        s = s.strip()
        # Remove backslash before commas: \, → ,
        s = re.sub(r'\\,', ',', s)
        # Remove backslash-space: \  →
        s = re.sub(r'\\ ', '', s)
        # Remove \; (small space)
        s = re.sub(r'\\;', '', s)
        # Remove \! (negative space)
        s = re.sub(r'\\!', '', s)
        # Collapse whitespace
        s = re.sub(r'\s+', '', s)
        return s

    na = normalize_escapes(a)
    nb = normalize_escapes(b)
    return na == nb


def candidate_f_composed_pipeline(a: str, b: str, tol: float = 0.01) -> bool:
    """(f) Composed pipeline: whitespace → escapes → LaTeX → coordinates → compare."""
    def normalize_composed(s):
        s = s.strip()
        # Step 1: Whitespace collapse
        s = re.sub(r'\s+', ' ', s)
        # Step 2: Backslash-escape stripping
        s = re.sub(r'\\,', ',', s)
        s = re.sub(r'\\ ', '', s)
        s = re.sub(r'\\;', '', s)
        s = re.sub(r'\\!', '', s)
        # Step 3: LaTeX normalization
        s = re.sub(
            r'\\frac\s*\{\s*([^}]+)\s*\}\s*\{\s*([^}]+)\s*\}',
            r'\1/\2',
            s
        )
        s = re.sub(r'\\infty', 'inf', s, flags=re.IGNORECASE)
        s = re.sub(r'\\displaystyle', '', s)
        s = re.sub(r'\\text\s*\{\s*([^}]*)\s*\}', r'\1', s)
        s = re.sub(r'\\mathrm\s*\{\s*([^}]*)\s*\}', r'\1', s)
        # Collapse internal whitespace again after LaTeX processing
        s = re.sub(r'\s+', '', s)
        return s

    def extract_coords(s):
        """Extract (a, b) or [a, b] coordinates."""
        s = s.strip()
        # Try parentheses
        m = re.match(r'^\(([^,]+),([^)]+)\)$', s)
        if m:
            try:
                x = float(m.group(1).strip())
                y = float(m.group(2).strip())
                return (x, y)
            except ValueError:
                pass
        # Try brackets
        m = re.match(r'^\[([^,]+),([^\]]+)\]$', s)
        if m:
            try:
                x = float(m.group(1).strip())
                y = float(m.group(2).strip())
                return (x, y)
            except ValueError:
                pass
        return None

    def within_tol(v1, v2):
        if v2 == 0:
            return abs(v1) < tol
        rel_err = abs(v1 - v2) / max(abs(v1), abs(v2), 1e-10)
        return rel_err < tol

    # Normalize both
    na = normalize_composed(a)
    nb = normalize_composed(b)

    # Step 5a: Exact match after normalization
    if na == nb:
        return True

    # Step 5b: Try coordinate extraction
    ca = extract_coords(na)
    cb = extract_coords(nb)
    if ca and cb:
        xa, ya = ca
        xb, yb = cb
        return within_tol(xa, xb) and within_tol(ya, yb)

    # Step 5c: Fallback to normalized string comparison
    return na == nb


def compute_consensus_with_matcher(extractions: dict, matcher_fn) -> dict:
    """Compute agreement using a custom matcher function instead of answers_match."""
    # Exclude empty extractions
    valid = {t: a for t, a in extractions.items() if a}
    if not valid:
        return {"type": "0/0", "which_agreed": [], "answer": ""}

    teachers = list(valid.keys())
    answers = list(valid.values())

    # Build agreement groups using pairwise matcher
    groups = []
    assigned = set()
    for i, t in enumerate(teachers):
        if t in assigned:
            continue
        group = [t]
        assigned.add(t)
        for j in range(i + 1, len(teachers)):
            if teachers[j] not in assigned:
                if matcher_fn(answers[i], answers[j]):
                    group.append(teachers[j])
                    assigned.add(teachers[j])
        groups.append(group)

    # Find largest group
    largest = max(groups, key=len)
    count = len(largest)
    total = len(valid)
    type_str = f"{count}/{total}"

    return {
        "type": type_str,
        "which_agreed": largest,
        "answer": valid[largest[0]],
    }


def main():
    manifest = load_manifest()

    # Filter to 1/3 and 2/3 items (false-disagreement candidates)
    candidates = [e for e in manifest if e.get("agreement_type") in ["1/3", "2/3"]]
    print(f"Total manifest entries: {len(manifest)}")
    print(f"Candidates (1/3 + 2/3): {len(candidates)}")
    print(f"  1/3: {sum(1 for e in manifest if e.get('agreement_type') == '1/3')}")
    print(f"  2/3: {sum(1 for e in manifest if e.get('agreement_type') == '2/3')}")
    print()

    # Test each candidate normalization
    candidates_list = [
        ("(a) Whitespace collapse", candidate_a_whitespace_collapse),
        ("(b) Coordinate pairs (parens)", candidate_b_coordinate_pairs_parens),
        ("(c) Coordinate pairs (parens+brackets)", candidate_c_coordinate_pairs_brackets),
        ("(d) LaTeX normalizations", candidate_d_latex_normalizations),
        ("(e) Backslash-escape stripping", candidate_e_backslash_escapes),
        ("(f) Composed pipeline", candidate_f_composed_pipeline),
    ]

    print("=" * 80)
    print("AUDIT RESULTS: False-Disagreement Recovery by Candidate Normalization")
    print("=" * 80)
    print()

    results = {}
    for name, matcher_fn in candidates_list:
        flipped = []
        for item in candidates:
            item_id = item["id"]
            # Extract teacher answers
            extractions = {
                "gpt5_4": item.get("gpt5_4_answer_raw", ""),
                "gpt_oss": item.get("gpt_oss_answer_raw", ""),
                "sonnet": item.get("sonnet_answer_raw", ""),
            }

            # Compute with custom matcher
            new_consensus = compute_consensus_with_matcher(extractions, matcher_fn)
            new_type = new_consensus["type"]
            old_type = item["agreement_type"]

            # Check if agreement improved
            old_count = int(old_type.split("/")[0])
            new_count = int(new_type.split("/")[0])

            if new_count > old_count:
                flipped.append({
                    "item_id": item_id,
                    "old_type": old_type,
                    "new_type": new_type,
                    "question_type": item.get("question_type", "unknown"),
                })

        results[name] = flipped

        print(f"{name}:")
        print(f"  Items flipped to higher agreement: {len(flipped)}")
        if flipped:
            # Breakdown by old agreement type
            by_old_type = Counter(f["old_type"] for f in flipped)
            for atype in sorted(by_old_type.keys()):
                count = by_old_type[atype]
                print(f"    From {atype}: {count}")

            # Sample items
            samples = flipped[:5]
            print(f"  Sample items:")
            for sample in samples:
                print(
                    f"    Item {sample['item_id']}: {sample['question_type']} "
                    f"{sample['old_type']} → {sample['new_type']}"
                )
        print()

    # Summary: which candidate recovers the most?
    print("=" * 80)
    print("SUMMARY: Effectiveness by Candidate")
    print("=" * 80)
    for name, flipped in results.items():
        pct = 100 * len(flipped) / len(candidates) if candidates else 0
        print(f"{name}: {len(flipped):3d} items flipped ({pct:5.1f}%)")

    print()
    print("=" * 80)
    print("DETAILED SAMPLES: Top patterns by candidate")
    print("=" * 80)
    print()

    for name, flipped in results.items():
        if flipped:
            print(f"\n{name} — Top 10 samples:")
            for i, sample in enumerate(flipped[:10], 1):
                item = next(e for e in manifest if e["id"] == sample["item_id"])
                print(f"\n  {i}. Item {sample['item_id']} ({sample['question_type']})")
                print(f"     Agreement: {sample['old_type']} → {sample['new_type']}")
                print(f"     gpt5_4:  {item['gpt5_4_answer_raw']!r}")
                print(f"     gpt_oss: {item['gpt_oss_answer_raw']!r}")
                print(f"     sonnet:  {item['sonnet_answer_raw']!r}")

    print()
    print("=" * 80)
    print("END AUDIT")
    print("=" * 80)


if __name__ == "__main__":
    main()
