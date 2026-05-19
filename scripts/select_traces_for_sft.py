#!/usr/bin/env python3
"""
Build SFT v3 dataset with adaptive trace selection.
Selects optimal single trace per item using question-type-specific priority rules.
Inputs: correctness_labels (from Ticket 5), teacher responses
Outputs: sft_v3_dataset_<timestamp>.jsonl with selected traces
"""

import sys
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml
from src.storage import read_jsonl

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Reasoning keywords check
REASONING_KEYWORDS = {
    "Derivation", "Deriv", "Step", "Therefore", "Thus", "Hence", "So",
    "Conclude", "Result", "Answer", "Solve", "Simplify", "Expand", "Factor",
    "Rearrange", "Substitute", "Equation", "Expression", "Formula", "Calculate"
}


def has_reasoning(response: str) -> bool:
    """Heuristic check for reasoning presence."""
    if not response or len(response) < 100:
        return False
    response_lower = response.lower()
    return any(keyword.lower() in response_lower for keyword in REASONING_KEYWORDS)


def has_boxed(response: str) -> bool:
    """Check if response has exactly one well-formed \\boxed{}."""
    count = response.count(r"\boxed{")
    return count == 1


def extract_response_section(md_content: str) -> str:
    """Extract 'Reasoning + Response' section from markdown."""
    lines = md_content.split("\n")
    in_section = False
    content = []

    for line in lines:
        if "## Reasoning + Response" in line:
            in_section = True
            continue
        if in_section and line.startswith("##"):
            break
        if in_section:
            content.append(line)

    return "\n".join(content).strip()


def count_tokens_estimate(text: str) -> int:
    """Rough estimate of token count (1 token ~ 4 chars)."""
    return len(text) // 4


def truncate_with_boxed(text: str, max_tokens: int = 4000) -> tuple[str, bool]:
    """
    Truncate text to max_tokens while preserving final \\boxed{}.
    Returns: (truncated_text, was_truncated)
    """
    if count_tokens_estimate(text) <= max_tokens:
        return text, False

    # Find last \\boxed{}
    boxed_pattern = r"\\boxed\{[^}]*\}"
    matches = list(re.finditer(boxed_pattern, text))

    if not matches:
        # No boxed, just truncate
        target_chars = max_tokens * 4
        return text[:target_chars], True

    last_match = matches[-1]
    boxed_start = last_match.start()
    boxed_text = text[boxed_start:]

    # Keep everything up to boxed, then the boxed answer
    target_chars = (max_tokens - count_tokens_estimate(boxed_text)) * 4
    truncated = text[:target_chars].rstrip() + "\n\n" + boxed_text

    return truncated, True


def load_config() -> dict:
    """Load config.yaml."""
    config_file = Path(__file__).parent.parent / "config.yaml"
    with open(config_file) as f:
        return yaml.safe_load(f)


def load_teacher_response(item_dir: Path, teacher: str) -> tuple[str, int]:
    """
    Load teacher response and return content + estimated tokens.
    Returns: (response_text, estimated_tokens)
    """
    response_file = item_dir / f"{teacher}_response.md"
    metadata_file = item_dir / f"{teacher}_metadata.json"

    if not response_file.exists():
        return "", 0

    with open(response_file) as f:
        content = f.read()

    # Try to load actual token count from metadata
    tokens = 0
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
                tokens = metadata.get("output_tokens", 0)
        except:
            tokens = count_tokens_estimate(content)
    else:
        tokens = count_tokens_estimate(content)

    return content, tokens


def select_trace(
    item: dict,
    output_dir: Path,
    labels_by_id: dict
) -> dict | None:
    """
    Select best trace for item using question-type-specific rules.

    Returns:
        {
            "id": int,
            "question": str,
            "question_type": str,
            "label_answer": str,
            "label_confidence": "HIGH" | "MEDIUM",
            "trace_source": "sonnet" | "gpt5_4" | "gpt_oss" | None,
            "trace": str,
            "trace_truncated": bool,
            "trace_output_tokens": int
        }
        or None if item should be dropped
    """
    item_id = item["id"]
    question_type = item["question_type"]
    label_entry = labels_by_id.get(item_id)

    if not label_entry or label_entry["label"] == "DROP":
        return None

    label_answer = label_entry["label_answer"]
    label_confidence = label_entry["label"]  # HIGH or MEDIUM

    # Get item directory
    item_dir = output_dir / f"item_{int(item_id):04d}"
    if not item_dir.exists():
        return None

    # Load all teacher responses
    teachers_data = {}
    for teacher in ["sonnet", "gpt5_4", "gpt_oss"]:
        content, tokens = load_teacher_response(item_dir, teacher)
        if content:
            md_section = extract_response_section(content)
            teachers_data[teacher] = {
                "md_content": content,
                "section": md_section,
                "tokens": tokens,
                "has_reasoning": has_reasoning(md_section),
                "has_boxed": has_boxed(md_section),
            }

    # Priority rules per question type
    if question_type == "mcq":
        priority = ["gpt5_4", "sonnet", "gpt_oss"]
    else:  # single_free or multi_free
        priority = ["sonnet", "gpt5_4", "gpt_oss"]

    # Select best trace
    for teacher in priority:
        if teacher not in teachers_data:
            continue

        data = teachers_data[teacher]

        # Check criteria: has reasoning AND has boxed
        if not (data["has_reasoning"] and data["has_boxed"]):
            continue

        # For single/multi_free, require min output tokens
        if question_type != "mcq" and data["tokens"] < 200:
            continue

        # Get trace section
        trace = data["section"]

        # Truncate if needed (GPT-OSS max 4000 tokens)
        trace_truncated = False
        if teacher == "gpt_oss" and data["tokens"] > 4000:
            trace, trace_truncated = truncate_with_boxed(trace, max_tokens=4000)

        return {
            "id": item_id,
            "question": item.get("question", ""),
            "question_type": question_type,
            "label_answer": label_answer,
            "label_confidence": label_confidence,
            "trace_source": teacher,
            "trace": trace,
            "trace_truncated": trace_truncated,
            "trace_output_tokens": data["tokens"],
        }

    # No eligible trace found
    return None


def main():
    """Build SFT v3 dataset."""
    logger.info("=== Building SFT v3 Dataset ===")

    config = load_config()
    output_dir = Path(config["paths"]["output_dir"])

    # Find latest correctness labels file
    labels_files = sorted(output_dir.glob("correctness_labels_*.json"))
    if not labels_files:
        logger.error("No correctness_labels file found")
        return 1

    labels_file = labels_files[-1]
    logger.info(f"Using labels: {labels_file}")

    # Load labels
    with open(labels_file) as f:
        labels_list = json.load(f)

    labels_by_id = {l["id"]: l for l in labels_list}
    logger.info(f"Loaded {len(labels_by_id)} labels")

    # Load manifest to get question_type
    manifest_path = output_dir / config["paths"]["manifest_file"]
    manifest = read_jsonl(manifest_path)
    manifest_by_id = {m["id"]: m for m in manifest}

    # Build dataset
    dataset = []
    dropped = 0
    by_source = defaultdict(int)
    by_confidence = defaultdict(int)
    by_type = defaultdict(int)
    truncated_count = 0

    for label_entry in labels_list:
        item_id = label_entry["id"]
        question_type = label_entry.get("question_type", "unknown")

        # Reconstruct item dict
        item = {
            "id": item_id,
            "question": label_entry.get("question", ""),
            "question_type": question_type,
        }

        # Select trace
        trace_entry = select_trace(item, output_dir, labels_by_id)

        if trace_entry is None:
            dropped += 1
            continue

        dataset.append(trace_entry)
        by_source[trace_entry["trace_source"]] += 1
        by_confidence[trace_entry["label_confidence"]] += 1
        by_type[question_type] += 1
        if trace_entry["trace_truncated"]:
            truncated_count += 1

    logger.info(f"Built dataset: {len(dataset)} items ({dropped} dropped)")

    # Save dataset
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_file = output_dir / f"sft_v3_dataset_{timestamp}.jsonl"

    with open(dataset_file, "w") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")

    logger.info(f"Saved SFT v3 dataset: {dataset_file}")

    # Print summary
    print("\n" + "="*80)
    print("SFT V3 DATASET SUMMARY")
    print("="*80)
    print(f"\nTotal items: {len(dataset)}")
    print(f"Dropped: {dropped}")

    print(f"\nBreakdown by Trace Source:")
    for source in sorted(by_source.keys()):
        count = by_source[source]
        pct = 100 * count / max(len(dataset), 1)
        print(f"  {source:15s}: {count:3d} ({pct:5.1f}%)")

    print(f"\nBreakdown by Label Confidence:")
    for conf in sorted(by_confidence.keys()):
        count = by_confidence[conf]
        pct = 100 * count / max(len(dataset), 1)
        print(f"  {conf:15s}: {count:3d} ({pct:5.1f}%)")

    print(f"\nBreakdown by Question Type:")
    for q_type in sorted(by_type.keys()):
        count = by_type[q_type]
        pct = 100 * count / max(len(dataset), 1)
        print(f"  {q_type:15s}: {count:3d} ({pct:5.1f}%)")

    print(f"\nTruncated traces (GPT-OSS >4000 tokens): {truncated_count}")

    print(f"\n{'='*80}")
    print(f"Output: {dataset_file}")
    print("="*80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
