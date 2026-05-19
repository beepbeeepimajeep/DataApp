"""
Normalization layer for cross-teacher answer comparison.

Used ONLY for consensus computation. Raw extraction stays unchanged for Kaggle.
Handles formatting differences: whitespace, units, LaTeX variants, numeric tolerance.
"""

import re
import math


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
    """Compare two answers with normalization and numeric tolerance.

    Returns True if answers are equivalent:
    - Exact string match after normalization
    - Numeric equivalence within tolerance
    - LaTeX fraction equivalence (including decimal vs fraction)

    For multi-answers (comma-separated), compares element-wise.
    """
    if not a or not b:
        return a == b

    # Normalize both
    na = normalize_for_consensus(a)
    nb = normalize_for_consensus(b)

    # Exact match
    if na == nb:
        return True

    # Multi-answer comparison: split on top-level commas and compare each
    if ',' in na or ',' in nb:
        parts_a = _split_top_level_commas(na)
        parts_b = _split_top_level_commas(nb)
        if len(parts_a) != len(parts_b):
            return False
        return all(answers_match(pa, pb, tolerance) for pa, pb in zip(parts_a, parts_b))

    # Try numeric comparison (covers decimals, integers, simple fractions)
    # Also try to evaluate LaTeX fractions as decimals
    va = _try_parse_numeric(na)
    if va is None:
        va = _try_eval_latex_frac(na)

    vb = _try_parse_numeric(nb)
    if vb is None:
        vb = _try_eval_latex_frac(nb)

    if va is not None and vb is not None:
        return _numeric_equal(va, vb, tolerance)

    # No match
    return False


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
