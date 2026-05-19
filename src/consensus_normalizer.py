"""
Consensus comparison for teacher answer agreement.

SCOPE BOUNDARY:
This module's matching logic determines whether teachers SEMANTICALLY
agree (e.g., (a,b) vs [a,b] with same numerical values are considered
agreement). This is for correctness labeling (Ticket 5).

IT IS NOT a canonical format normalizer for training data construction
(Ticket 6). For Kaggle grading, format matters:
- Order within items matters (set-matched items may have different order)
- LaTeX vs decimal precision conventions must match gold exactly
- Parentheses vs brackets vs braces have different Kaggle interpretations

When agreement_via == "set_match" or "coord_pair", items agree on
VALUES but not on FORMAT. Ticket 6 (SFT data construction) must apply
canonical format normalization on selected traces, not rely on this
module for that.

Raw extraction stays unchanged in outputs. This module ONLY affects
consensus voting, not final answer representation.
"""

import re
import math
import logging

logger = logging.getLogger(__name__)


def _split_top_level_commas(s: str) -> list[str]:
    """Split string on top-level commas only.

    Commas inside (), [], {} are not split points.
    Handles LaTeX braces and parens correctly.

    Examples:
        'a,b,c' → ['a', 'b', 'c']
        '(3,4)' → ['(3,4)']
        '\\frac{1,2}{3}' → ['\\frac{1,2}{3}']
        '(0,1), (2,3)' → ['(0,1)', '(2,3)']
    """
    if not s:
        return ['']

    parts = []
    depth = 0
    current = []
    for ch in s:
        if ch in '([{':
            depth += 1
            current.append(ch)
        elif ch in ')]}':
            depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0:
            parts.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append(''.join(current).strip())
    return parts if parts else ['']


def normalize_for_consensus(raw: str) -> str:
    """Normalize extracted answer for cross-teacher comparison only.

    NOT used for Kaggle submission. Only for computing agreement.
    """
    s = raw.strip()
    if not s:
        return ""

    # 1. Strip trailing units (common: ft, lb, days, dollars, etc.)
    s = re.sub(r'\s*(ft|lb|lbs|days|dollars|hours|minutes|seconds|mm|cm|m|kg|oz)\s*$', '', s, flags=re.IGNORECASE)

    # 2. Strip LaTeX display wrappers
    s = s.replace('\\,', '').replace('\\ ', '').replace('\\!', '')
    # Clean up text blocks carefully
    s = re.sub(r'\\text\{([^}]*)\}', r'\1', s)

    # 3. Normalize whitespace around commas (multi-answer)
    #    "2, 302" → "2,302"
    s = re.sub(r'\s*,\s*', ',', s)

    # 4. Normalize LaTeX fraction shorthand (no spaces allowed inside)
    #    \frac34 → \frac{3}{4}
    s = re.sub(r'\\frac\s*(\d)\s*(\d)', r'\\frac{\1}{\2}', s)

    # 5. Strip \dfrac → \frac
    s = s.replace('\\dfrac', '\\frac')
    s = s.replace('\\displaystyle', '')

    # 6. Strip "approximately" language
    s = re.sub(r'\s*\(?approximately\)?\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s*\(approx[.\s]*\)', '', s, flags=re.IGNORECASE)

    # 7. Normalize internal whitespace only (not around braces)
    #    Collapse multiple spaces but preserve brace structure
    s = re.sub(r'(?<!\{)\s+(?!\})', ' ', s)  # collapse spaces except adjacent to braces
    s = re.sub(r'\s*\}\s*', '}', s)  # remove spaces around closing brace
    s = re.sub(r'\s*\{\s*', '{', s)  # remove spaces around opening brace
    s = s.strip()

    return s


def answers_match(a: str, b: str, tolerance: float = 0.01) -> bool:
    """Compare two answers with composed normalization and numeric tolerance.

    Returns True if answers are equivalent:
    - Exact string match after normalization
    - Coordinate pairs (a,b) and [a,b] with numerical tolerance
    - Multi-answers as sets (order-independent)
    - Numeric equivalence within tolerance
    - LaTeX fraction equivalence (including decimal vs fraction)

    Recursion guard: on RecursionError, falls back to literal string comparison.

    For match type tracking, use answers_match_with_type() instead.
    """
    try:
        result, _ = _answers_match_impl(a, b, tolerance)
        return result
    except RecursionError:
        # Fallback: compare as literal strings (no normalization)
        return a.strip() == b.strip()


def answers_match_with_type(a: str, b: str, tolerance: float = 0.01) -> tuple[bool, str]:
    """Compare answers and return match type for agreement tracking.

    Returns:
        (match: bool, match_type: str)

    match_type is one of:
      - "exact": raw strings equal after strip
      - "normalized": matched after escape/whitespace/LaTeX normalization
      - "coord_pair": matched via coordinate-pair extraction + tolerance
      - "set_match": matched as unordered sets (multi-answer)
      - "numeric": matched as numbers within tolerance
      - "no_match": did not match
    """
    try:
        return _answers_match_impl(a, b, tolerance)
    except RecursionError:
        # Fallback: compare as literal strings
        if a.strip() == b.strip():
            return (True, "fallback_literal")
        return (False, "no_match")


def _normalize_aggressively(s: str) -> str:
    """Apply composed normalization pipeline.

    Step A: Whitespace + escape + unit normalization
    Step B: LaTeX structural normalization
    Step C: Normalize to canonical forms
    """
    s = s.strip()
    if not s:
        return ""

    # Step A: Aggressive whitespace + escape + unit normalization
    # Strip trailing units (ft, lb, days, dollars, etc.)
    s = re.sub(
        r'\s*(ft|lb|lbs|days|dollars|hours|minutes|seconds|mm|cm|m|kg|oz)\s*$',
        '',
        s,
        flags=re.IGNORECASE
    )

    # Strip all LaTeX space escapes
    s = re.sub(r'\\,', '', s)        # \, (thin space) → (remove)
    s = re.sub(r'\\ ', ' ', s)       # \  (backslash-space) → space
    s = re.sub(r'\\;', ' ', s)       # \; (medium space) → space
    s = re.sub(r'\\!', '', s)        # \! (negative space) → (remove)
    s = re.sub(r'\\quad', ' ', s)    # \quad → space
    s = re.sub(r'\\qquad', '  ', s)  # \qquad → 2 spaces
    s = s.replace('~', ' ')          # ~ (tie/non-breaking space) → space

    # Strip "approximately" language before LaTeX processing
    s = re.sub(r'\s*\(?approximately\)?\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s*\(approx[.\s]*\)', '', s, flags=re.IGNORECASE)

    # Step B: LaTeX structural normalization (before whitespace collapse)
    # Remove braces around sqrt to avoid nested-brace matching issues
    # \sqrt{3} → \sqrt3 (allows \frac{\sqrt{3}}{2} → \frac{\sqrt3}{2} → \sqrt3/2)
    s = re.sub(r'\\sqrt\{(\d+)\}', r'\\sqrt\1', s)

    # Normalize LaTeX fraction shorthand: \frac34 → \frac{3}{4}
    s = re.sub(r'\\frac\s*(\d)\s*(\d)', r'\\frac{\1}{\2}', s)
    # \frac{a}{b} → a/b
    s = re.sub(
        r'\\frac\s*\{\s*([^}]+)\s*\}\s*\{\s*([^}]+)\s*\}',
        r'\1/\2',
        s
    )
    # \dfrac → \frac (for compatibility)
    s = s.replace('\\dfrac', '\\frac')
    # \infty variants → inf
    s = re.sub(r'\\infty', 'inf', s, flags=re.IGNORECASE)
    s = re.sub(r'\binf(inity)?\b', 'inf', s, flags=re.IGNORECASE)
    # Strip exponent braces: 5x^{4} → 5x^4
    s = re.sub(r'\^\{(\d+)\}', r'^\1', s)
    # Strip \displaystyle, \text{}, \mathrm{}
    s = re.sub(r'\\displaystyle\s*', '', s)
    s = re.sub(r'\\text\s*\{\s*([^}]*)\s*\}', r'\1', s)
    s = re.sub(r'\\mathrm\s*\{\s*([^}]*)\s*\}', r'\1', s)

    # Step C: Final whitespace normalization - collapse ALL whitespace
    s = re.sub(r'\s+', '', s)
    return s


def _try_extract_coordinate_pair(s: str) -> tuple[float, float] | None:
    """Extract (a, b) or [a, b] as numeric pair.

    After aggressive normalization, coordinates will be (a,b) or [a,b] with no spaces.
    """
    s = s.strip()

    # Try parentheses: (a,b) — no spaces after normalization
    m = re.match(r'^\(([^,]+),([^)]+)\)$', s)
    if m:
        try:
            x = float(m.group(1))
            y = float(m.group(2))
            return (x, y)
        except (ValueError, AttributeError):
            pass

    # Try brackets: [a,b] — no spaces after normalization
    m = re.match(r'^\[([^,]+),([^\]]+)\]$', s)
    if m:
        try:
            x = float(m.group(1))
            y = float(m.group(2))
            return (x, y)
        except (ValueError, AttributeError):
            pass

    return None


def _coordinates_equal(
    c1: tuple[float, float],
    c2: tuple[float, float],
    tolerance: float = 0.01
) -> bool:
    """Compare two coordinate pairs with numerical tolerance."""
    x1, y1 = c1
    x2, y2 = c2

    def within_tol(v1, v2):
        if v2 == 0:
            return abs(v1) < tolerance
        rel_err = abs(v1 - v2) / max(abs(v1), abs(v2), 1e-10)
        return rel_err < tolerance

    return within_tol(x1, x2) and within_tol(y1, y2)


def _answers_match_impl(
    a: str, b: str, tolerance: float = 0.01
) -> tuple[bool, str]:
    """Implementation of answers_match with composed pipeline.

    Returns:
        (match: bool, match_type: str)
    """
    # Apply composed normalization first
    na = _normalize_aggressively(a)
    nb = _normalize_aggressively(b)

    # After normalization, check for empty/falsy
    if not na and not nb:
        return (True, "exact")
    if not na or not nb:
        return (False, "no_match")

    # Exact match after normalization
    if na == nb:
        return (True, "normalized")

    # Try coordinate pair matching (both must be pairs)
    coord_a = _try_extract_coordinate_pair(na)
    coord_b = _try_extract_coordinate_pair(nb)
    if coord_a and coord_b:
        if _coordinates_equal(coord_a, coord_b, tolerance):
            return (True, "coord_pair")

    # Multi-answer comparison: handle as sets (order-independent)
    if ',' in na and ',' in nb:
        parts_a = _split_top_level_commas(na)
        parts_b = _split_top_level_commas(nb)

        # Set comparison: same elements regardless of order
        if len(parts_a) != len(parts_b):
            return (False, "no_match")

        # Match each element from parts_a to parts_b
        # Using set matching (each element must have a match)
        used_b = set()
        for pa in parts_a:
            found = False
            for i, pb in enumerate(parts_b):
                if i not in used_b:
                    match_result, _ = _answers_match_impl(pa, pb, tolerance)
                    if match_result:
                        used_b.add(i)
                        found = True
                        break
            if not found:
                return (False, "no_match")
        return (True, "set_match")

    # Single element comparison: try numeric
    va = _try_parse_numeric(na)
    if va is None:
        va = _try_eval_latex_frac(na)

    vb = _try_parse_numeric(nb)
    if vb is None:
        vb = _try_eval_latex_frac(nb)

    if va is not None and vb is not None:
        if _numeric_equal(va, vb, tolerance):
            return (True, "numeric")

    # No match
    return (False, "no_match")


def _try_parse_numeric(s: str) -> float | None:
    """Try to parse string as a number."""
    try:
        # Strip any remaining whitespace
        s = s.strip()
        return float(s)
    except ValueError:
        return None


def _try_eval_latex_frac(s: str) -> float | None:
    """Try to evaluate simple LaTeX fractions like \\frac{19}{33}."""
    s = s.strip()

    # LaTeX form: \frac{num}{denom}
    m = re.match(r'^\\frac\s*\{\s*([^}]+)\s*\}\s*\{\s*([^}]+)\s*\}$', s)
    if m:
        try:
            num = float(m.group(1).strip())
            den = float(m.group(2).strip())
            if den != 0:
                return num / den
        except ValueError:
            pass

    # Simple a/b format
    m = re.match(r'^(-?\d+(?:\.\d+)?)\s*/\s*(-?\d+(?:\.\d+)?)$', s)
    if m:
        try:
            num = float(m.group(1))
            den = float(m.group(2))
            if den != 0:
                return num / den
        except ValueError:
            pass

    return None


def _numeric_equal(a: float, b: float, tolerance: float = 0.01) -> bool:
    """Compare two floats with relative tolerance."""
    if b == 0:
        return abs(a) < tolerance
    rel_error = abs(a - b) / max(abs(a), abs(b), 1e-10)
    return rel_error < tolerance
