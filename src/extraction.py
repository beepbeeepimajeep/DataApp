"""
Answer extraction wrapper using competition repo's judger.py logic.
Imports Judger and provides DataApp-compatible interface.
"""

import sys
from pathlib import Path
from typing import Optional

# Import Judger from competition repo
COMP_REPO = Path(__file__).parent.parent.parent / "151B_SP26_Competition"
sys.path.insert(0, str(COMP_REPO))

from judger import Judger


class DataAppExtractor:
    """Wraps Judger for DataApp answer extraction."""

    def __init__(self, strict_extract: bool = False):
        """
        Initialize extractor.

        Args:
            strict_extract: If False, allows fallback to last formula/number.
        """
        self.judger = Judger(strict_extract=strict_extract)

    def extract(self, response: str) -> str:
        """
        Extract answer from model response.

        Returns:
            Extracted answer string, or "" if no answer found.
        """
        return self.judger.extract_ans(response)

    def extract_boxed(self, response: str) -> str:
        """Extract from \\boxed{} only (strict mode)."""
        return self.judger.extract_boxed_answer(response)

    def extract_all_boxed_list(self, response: str) -> list[str]:
        """Return list of all \\boxed{} entries (last contiguous group)."""
        return self.judger.extract_all_boxed(response)

    def normalize(self, answer: str) -> str:
        """Normalize answer for comparison."""
        return self.judger.normalize_answer(answer)

    def has_boxed(self, response: str) -> bool:
        """Check if response contains \\boxed{}."""
        return "\\boxed{" in response

    def count_boxed(self, response: str) -> int:
        """Count top-level \\boxed{} entries."""
        entries = self.judger.extract_all_boxed(response)
        return len(entries)
