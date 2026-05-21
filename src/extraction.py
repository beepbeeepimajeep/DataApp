"""
Answer extraction logic (ported from competition repo's judger.py + utils.py).
Self-contained, no external imports beyond stdlib. Windows-compatible.
"""

import re
from typing import Optional

# ─── Constants ───────────────────────────────────────────────────────────────

GSM8K_ANS_PREFIX = "#### "
PRM800K_ANS_PRRFIX = "# Answer\n\n"
NO_TRAILING_STRS = set(",.:;!?=\\.。，、；：！？")


# ─── Helper Functions ────────────────────────────────────────────────────────

def last_boxed_only_string(string: str) -> Optional[str]:
    """Return the last \\boxed{...} substring or None."""
    idx = string.rfind("\\boxed")
    if idx < 0:
        idx = string.rfind("\\fbox")
        if idx < 0:
            return None

    i = idx
    right_brace_idx = None
    num_open = 0
    while i < len(string):
        if string[i] == "{":
            num_open += 1
        elif string[i] == "}":
            num_open -= 1
            if num_open == 0:
                right_brace_idx = i
                break
        i += 1

    if right_brace_idx is None:
        return None
    return string[idx : right_brace_idx + 1]


def remove_boxed(s: Optional[str]) -> Optional[str]:
    """Strip \\boxed{ ... } wrapper and return inner content, or None on failure."""
    if s is None:
        return None
    for prefix in ("\\boxed{", "\\fbox{"):
        if s.startswith(prefix) and s.endswith("}"):
            return s[len(prefix) : -1]
    return None


def clean_trailing(s: str) -> str:
    """Removes trailing punctuation marks from a string."""
    s = str(s).strip()
    while s != "" and s[-1] in NO_TRAILING_STRS:
        s = s[:-1].strip()
    return s


def normalize_answer(content: str) -> str:
    """
    Normalize answer content from \\boxed{}.
    Ported from Judger.normalize_answer() - minimal version.
    """
    content = str(content).strip()

    # Normalize \dfrac and \tfrac to \frac
    content = content.replace("\\dfrac", "\\frac")
    content = content.replace("\\tfrac", "\\frac")

    # Remove \text{...} wrapper, keeping the content inside
    content = re.sub(r'\\text\{(.*?)\}', r'\1', content)
    content = re.sub(r'\\textbf\{(.*?)\}', r'\1', content)

    # Remove common special characters
    special_signal_map = {
        "\\left": "",
        "\\right": "",
        "∶": ":",
        "，": ",",
        "$": "",
        "\\approx": "=",
        "\\simeq": "=",
        "\\sim": "=",
        "^\\prime": "'",
        "^{\\prime}": "'",
    }
    for signal, replacement in special_signal_map.items():
        content = content.replace(signal, replacement)

    # Clean up whitespace
    content = content.strip()

    # --- Normalizations for comparison consistency ---
    # 1. Collapse whitespace around commas
    content = re.sub(r'\s*,\s*', ',', content)

    # 2. Collapse all internal whitespace to single space, then strip
    content = re.sub(r'\s+', ' ', content).strip()

    # 3. Remove LaTeX spacing commands
    for cmd in ['\\,', '\\;', '\\:', '\\!', '\\quad', '\\qquad',
                '\\hspace{1em}', '\\hspace{0.5em}', '\\enspace',
                '\\thinspace', '\\medspace', '\\thickspace']:
        content = content.replace(cmd, '')

    # 4. Remove \displaystyle
    content = content.replace('\\displaystyle', '')

    # 5. Final whitespace cleanup after LaTeX removal
    content = re.sub(r'\s+', ' ', content).strip()

    return content


def normalize_for_comparison(content: str) -> str:
    """Aggressive normalization used ONLY for answer comparison, never for output."""
    content = normalize_answer(str(content))
    # Remove ALL spaces
    content = content.replace(' ', '')
    # Uppercase
    content = content.upper()
    # Remove trailing periods
    content = content.rstrip('.')
    # Remove surrounding parens/brackets if they wrap the whole thing
    if content.startswith('(') and content.endswith(')'):
        inner = content[1:-1]
        if inner.count('(') == inner.count(')'):
            content = inner
    return content


# ─── Extraction Functions ────────────────────────────────────────────────────

def extract_all_boxed(text: str) -> list[str]:
    """
    Extract \\boxed{...} contents from the last contiguous group in text.
    Ported from Judger.extract_all_boxed()
    """
    entries = []
    start = 0
    while True:
        idx = text.find("\\boxed{", start)
        if idx < 0:
            break
        brace_start = idx + len("\\boxed{")
        depth = 1
        i = brace_start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        if depth == 0:
            content = text[brace_start : i - 1]
            if content:
                normalized = normalize_answer(content)
                entries.append((idx, i, normalized))
        start = i

    if not entries:
        return []

    # Take only the last contiguous group of \boxed{} answers.
    # Two boxed answers are "contiguous" if the text between them
    # contains only whitespace, commas, punctuation, $, or newlines.
    last_group = [entries[-1]]
    for j in range(len(entries) - 2, -1, -1):
        gap = text[entries[j][1] : entries[j + 1][0]]
        # Allow only whitespace, commas, $, and common separators between boxes
        if re.match(r"^[\s,\$\.\;\:\-\&\\]*$", gap):
            last_group.insert(0, entries[j])
        else:
            break

    return [e[2] for e in last_group]


def extract_boxed_answer(text: str) -> str:
    """
    Extract answer wrapped in \\boxed{} from model output.
    Ported from Judger.extract_boxed_answer()
    """
    # Strip thinking tags — only look at content after last </think>
    think_end = text.rfind("</think>")
    search_text = text[think_end + len("</think>") :] if think_end >= 0 else text

    # Try to extract all boxed answers from the final answer section
    all_boxed = extract_all_boxed(search_text)
    if len(all_boxed) > 1:
        return ", ".join(all_boxed)
    elif len(all_boxed) == 1:
        return all_boxed[0]

    # Fallback: last boxed only (search full text)
    boxed_str = last_boxed_only_string(text)
    content = remove_boxed(boxed_str)
    if content is not None:
        return normalize_answer(content)

    # Final fallback: try direct regex
    match = re.search(r"\\boxed{", text)
    if match:
        start_index = match.end()
        end_index = start_index
        stack = 1
        while stack > 0 and end_index < len(text):
            if text[end_index] == "{":
                stack += 1
            elif text[end_index] == "}":
                stack -= 1
            end_index += 1
        if stack == 0:
            content = text[start_index : end_index - 1]
            if content:
                return normalize_answer(content)

    return ""


def extract_explicit_ans(resp_str: str) -> Optional[str]:
    """
    Extract answer using keyword anchors.
    Ported from Judger.extract_explicit_ans()
    """
    resp_str = clean_trailing(resp_str)

    # might be answer only
    if "herefore" in resp_str:
        resp_str = resp_str.split("herefore")[-1].strip()
    if GSM8K_ANS_PREFIX in resp_str:
        resp_str = resp_str.split(GSM8K_ANS_PREFIX)[-1].strip()
    if PRM800K_ANS_PRRFIX in resp_str:
        resp_str = resp_str.split(PRM800K_ANS_PRRFIX)[-1].strip()

    if "oxed{" in resp_str:
        resp = extract_boxed_answer(resp_str)
    else:
        resp = resp_str

        # should be answer only
        if "is the ans" in resp:
            resp = re.split(r"(,|\.|\!\|?)", resp.split("is the ans")[-2].strip())[-1].strip()
        elif "is our ans" in resp:
            resp = re.split(r"(,|\.|\!\|?)", resp.split("is our ans")[-2].strip())[-1].strip()
        elif "answer is" in resp:
            resp = resp.split("answer is")[-1].strip()
        elif "answer:" in resp:
            resp = resp.split("answer:")[-1].strip()
        elif "answer :" in resp:
            resp = resp.split("answer :")[-1].strip()
        else:
            return None

        if resp.startswith("$") and resp.endswith("$"):
            resp = resp[1:-1]

    return resp


def count_top_level_answers(extracted: str) -> int:
    """
    Count top-level comma-separated values in extracted answer.
    Handles depth-aware splitting for interval notation.

    Example:
        '(-inf, 5), (-3, 5]' → 2 (two intervals, not 4 commas)
        '5, 10, 15' → 3 (three values)
    """
    if not extracted.strip():
        return 0

    depth = 0
    count = 1
    for char in extracted:
        if char in '([{':
            depth += 1
        elif char in ')]}':
            depth -= 1
        elif char == ',' and depth == 0:
            count += 1

    return count


def extract_ans(resp_str: str, strict_extract: bool = True) -> str:
    """
    Main entry point for answer extraction.
    Ported from Judger.extract_ans()
    """
    ans = extract_explicit_ans(resp_str)
    if ans is not None:
        return ans

    if not strict_extract:
        # Speculate with the last latex formula
        matches = re.findall(
            r"(?:\$|\\\(|\\\[)([^\$]+)(?:\$|\\\(|\\\[)", resp_str, re.DOTALL
        )
        if len(matches) > 0:
            return matches[-1]
        # Speculate with the last number
        matches = re.findall(r"-?\d*\.?\d+", resp_str.replace(",", ""))
        if len(matches) > 0:
            return matches[-1]

    return ""  # Empty str if no answer is found


# ─── Public API ──────────────────────────────────────────────────────────────

class DataAppExtractor:
    """Public API for answer extraction."""

    def __init__(self, strict_extract: bool = False):
        """
        Initialize extractor.

        Args:
            strict_extract: If True, only extract \\boxed{} answers.
                           If False, allow fallback to formulas/numbers.
        """
        self.strict_extract = strict_extract

    def extract(self, response: str) -> str:
        """
        Extract answer from response.

        Returns:
            Extracted answer string, or "" if none found.
        """
        return extract_ans(response, strict_extract=self.strict_extract)

    def has_boxed(self, response: str) -> bool:
        """Check if response contains \\boxed{}."""
        return "\\boxed{" in response

    def count_boxed(self, response: str) -> int:
        """Count number of \\boxed{} blocks (last contiguous group)."""
        return len(extract_all_boxed(response))
