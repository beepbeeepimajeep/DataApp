"""
Tests for consensus_normalizer.py fixes.

Covers:
- Composed normalization pipeline
- Coordinate pair matching with tolerance
- Multi-answer set comparison
- LaTeX normalization
- Escape handling
- Recursion safety
- Real disagreements
"""

import pytest
from src.consensus_normalizer import answers_match, answers_match_with_type


class TestExactMatches:
    """Exact string matches return 'exact' match_type."""

    def test_exact_single_value(self):
        """'42' ↔ '42' → (True, 'exact')."""
        result, match_type = answers_match_with_type("42", "42")
        assert result is True
        assert match_type == "exact"

    def test_exact_coordinate_pair(self):
        """'(12.30, 25.10)' ↔ '(12.30, 25.10)' → (True, 'exact')."""
        result, match_type = answers_match_with_type("(12.30, 25.10)", "(12.30, 25.10)")
        assert result is True
        assert match_type == "exact"

    def test_exact_multi_answer(self):
        """'1, 2, 3' ↔ '1, 2, 3' → (True, 'exact')."""
        result, match_type = answers_match_with_type("1, 2, 3", "1, 2, 3")
        assert result is True
        assert match_type == "exact"

    def test_exact_with_spaces(self):
        """'a, b, c' ↔ 'a, b, c' → (True, 'exact')."""
        result, match_type = answers_match_with_type("a, b, c", "a, b, c")
        assert result is True
        assert match_type == "exact"

    def test_exact_expression(self):
        """'y = 5x^4' ↔ 'y = 5x^4' → (True, 'exact')."""
        result, match_type = answers_match_with_type("y = 5x^4", "y = 5x^4")
        assert result is True
        assert match_type == "exact"

    def test_not_exact_whitespace_diff(self):
        """'y = 5x^4' ↔ 'y=5x^4' → (True, 'normalized' not 'exact')."""
        result, match_type = answers_match_with_type("y = 5x^4", "y=5x^4")
        assert result is True
        assert match_type == "normalized"  # Different raw strings, matched via normalization

    def test_not_exact_precision_diff(self):
        """'(12.30, 25.10)' ↔ '(12.3, 25.1)' → (True, 'coord_pair' not 'exact')."""
        result, match_type = answers_match_with_type("(12.30, 25.10)", "(12.3, 25.1)")
        assert result is True
        assert match_type in ("coord_pair", "normalized")  # Different raw strings


class TestCoordinatePairs:
    """Coordinate pair matching with numerical tolerance."""

    def test_coordinate_pairs_exact_match(self):
        """(12.30, 25.10) ↔ (12.3, 25.1) with tolerance."""
        assert answers_match("(12.30, 25.10)", "(12.3, 25.1)")

    def test_coordinate_pairs_with_precision_diff(self):
        """(12.30, 25.10) ↔ [12.306, 25.094] — different brackets, precision."""
        assert answers_match("(12.30, 25.10)", "[12.306, 25.094]")

    def test_coordinate_pairs_with_escapes(self):
        """(12.30,\\ 25.10) ↔ (12.3,\\;25.1) — escape variants."""
        assert answers_match("(12.30,\\ 25.10)", "(12.3,\\;25.1)")

    def test_coordinate_pairs_real_disagreement(self):
        """(1, 2) ↔ (1, 3) — real numerical disagreement."""
        assert not answers_match("(1, 2)", "(1, 3)")

    def test_coordinate_pairs_order_matters(self):
        """(a, b) ↔ (b, a) — coordinate order is significant."""
        assert not answers_match("(1, 2)", "(2, 1)")

    def test_single_bracket_pair(self):
        """[12.306, 25.094] ↔ (12.30, 25.10)."""
        assert answers_match("[12.306, 25.094]", "(12.30, 25.10)")


class TestLaTeXNormalization:
    """LaTeX structural normalization."""

    def test_frac_to_division(self):
        """\\frac{5}{6} ↔ 5/6."""
        assert answers_match("\\frac{5}{6}", "5/6")

    def test_exponent_brace_strip(self):
        """5x^{4} ↔ 5x^4."""
        assert answers_match("5x^{4}", "5x^4")

    def test_multi_answer_frac_forms(self):
        """Mixed fraction formats in multi-answer."""
        assert answers_match(
            "-\\frac{5}{6},\\frac{5}{6}",
            "-5/6,5/6"
        )

    def test_infty_variants(self):
        """\\infty → inf normalization."""
        assert answers_match("(0,\\infty)", "(0, inf)")


class TestMultiAnswerSetComparison:
    """Set-based comparison for multi-answer questions (order-independent)."""

    def test_set_order_independent(self):
        """-e^2, e^2 ↔ e^2, -e^2 — set equality."""
        assert answers_match("-e^2, e^2", "e^2, -e^2")

    def test_set_with_numbers(self):
        """1, 2, 3 ↔ 3, 1, 2 — set equality."""
        assert answers_match("1, 2, 3", "3, 1, 2")

    def test_set_cardinality_mismatch(self):
        """1, 2 ↔ 1, 2, 3 — different cardinality."""
        assert not answers_match("1, 2", "1, 2, 3")

    def test_set_element_mismatch(self):
        """1, 2 ↔ 1, 3 — different elements."""
        assert not answers_match("1, 2", "1, 3")

    def test_set_with_escapes(self):
        """Multi-answer with escape variants should match."""
        assert answers_match(
            "A,\\ C,\\ D",
            "A,\\;C,\\;D"
        )


class TestEscapeHandling:
    """Aggressive escape stripping."""

    def test_backslash_space(self):
        """Tommy,Chucky,February\\ 7 ↔ normal spacing."""
        # After escape stripping and whitespace collapse
        assert answers_match(
            "Tommy,Chucky,February\\ 7",
            "Tommy,Chucky,February 7"
        )

    def test_escape_variants_in_coords(self):
        """Coordinate pairs with different space escape variants."""
        assert answers_match(
            "(12.30,\\ 25.10)",
            "(12.3,\\;25.1)"
        )

    def test_multiple_escape_types(self):
        """Mix of \\, \\;, \\! in same string."""
        assert answers_match(
            "A,\\ C,\\;D,\\!E",
            "A, C, D, E"
        )


class TestRecursionSafety:
    """Recursion guard prevents crashes on malformed input."""

    def test_nested_fracs_no_crash(self):
        """(\\frac{1373}{2744},0),none ↔ (1373/2744,\\ 0),\\ none."""
        # Should not raise RecursionError
        result = answers_match(
            "(\\frac{1373}{2744},0),none",
            "(1373/2744,\\ 0),\\ none"
        )
        # May or may not match depending on parsing, but should not crash
        assert isinstance(result, bool)

    def test_deeply_nested_braces_no_crash(self):
        """Pathological brace nesting doesn't crash."""
        result = answers_match(
            "{{{a}}}",
            "{a}"
        )
        assert isinstance(result, bool)

    def test_escaped_braces_no_crash(self):
        """\\38{,}800.00 ↔ \\38,800.00 — no crash."""
        result = answers_match(
            "\\38{,}800.00",
            "\\38,800.00"
        )
        assert isinstance(result, bool)


class TestRealDisagreements:
    """True mathematical or choice disagreements remain disagreements."""

    def test_mcq_choices(self):
        """I ↔ B — different MCQ choices."""
        assert not answers_match("I", "B")

    def test_numeric_disagreement(self):
        """4 ↔ 7 — genuinely different answers."""
        assert not answers_match("4", "7")

    def test_partial_vs_complete_answer(self):
        """e^2 ↔ e^2, -e^2 — different cardinality of solution set."""
        assert not answers_match("e^2", "e^2, -e^2")

    def test_function_notation_mismatch(self):
        """P(t)=... ↔ ... (only RHS) — semantic difference, not formatting."""
        # This should NOT match: one includes function notation, one doesn't
        # This is a content difference, not formatting
        assert not answers_match("P(t)=2025t-4300", "2025t-4300")


class TestWhitespaceHandling:
    """Whitespace normalization in general expressions."""

    def test_operator_spacing(self):
        """D=800-50d ↔ D = 800 - 50d."""
        assert answers_match("D=800-50d", "D = 800 - 50d")

    def test_expression_spacing(self):
        """29x^7+6x^5 ↔ 29x^7 + 6x^5."""
        assert answers_match("29x^7+6x^5", "29x^7 + 6x^5")

    def test_inequality_spacing(self):
        """x>21250 ↔ x > 21250."""
        assert answers_match("x>21250", "x > 21250")


class TestEdgeCases:
    """Edge cases and corner cases."""

    def test_empty_strings(self):
        """Empty strings should match."""
        assert answers_match("", "")

    def test_single_space_vs_empty(self):
        """Single space ↔ empty (after normalization)."""
        assert answers_match(" ", "")

    def test_whitespace_only(self):
        """Strings of only whitespace should match."""
        # After aggressive normalization, both become empty strings
        assert answers_match("   ", "")

    def test_none_handling(self):
        """None or falsy values handled gracefully."""
        assert not answers_match("", "a")
        assert not answers_match("a", "")

    def test_unicode_mathematical_operators(self):
        """Mathematical Unicode operators (if present) should normalize."""
        # Example: × (multiplication) vs x, ÷ vs /
        # For now, just ensure no crash
        result = answers_match("a × b", "a * b")
        assert isinstance(result, bool)
