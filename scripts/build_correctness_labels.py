#!/usr/bin/env python3
"""
Build correctness labels using 4-teacher + run14b SC dual-signal approach.
Inputs: Phase 2 manifest (3-teacher), GPT-5.5 full responses, run14b SC results.
Outputs: correctness_labels, conflict_items, per-teacher accuracy stats.
"""

import sys
import json
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import yaml
from src.storage import read_jsonl
from src.orchestrator import compute_consensus
from src.extraction import DataAppExtractor
from src.consensus_normalizer import answers_match

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_config() -> dict:
    """Load config.yaml."""
    config_file = Path(__file__).parent.parent / "config.yaml"
    with open(config_file) as f:
        return yaml.safe_load(f)


def load_run14b_data(run14b_path: Path) -> dict:
    """Load run14b SC results indexed by item ID."""
    run14b = {}
    if not run14b_path.exists():
        logger.warning(f"run14b file not found: {run14b_path}")
        return run14b

    for entry in read_jsonl(run14b_path):
        item_id = entry.get("id")
        if item_id is not None:
            run14b[item_id] = entry

    logger.info(f"Loaded {len(run14b)} items from run14b")
    return run14b


def load_gpt55_response(gpt55_dir: Path, item_id: int) -> str:
    """Load GPT-5.5 response markdown file."""
    response_file = gpt55_dir / f"item_{int(item_id):04d}_gpt5_5_response.md"
    if response_file.exists():
        with open(response_file) as f:
            return f.read()
    return ""


def extract_gpt55_answer(response_text: str, extractor: DataAppExtractor) -> str:
    """Extract answer from GPT-5.5 response."""
    if not response_text:
        return ""
    return extractor.extract(response_text)


def compute_labels(
    manifest: list[dict],
    run14b: dict,
    gpt55_dir: Path,
    output_dir: Path
) -> tuple[list[dict], list[dict]]:
    """
    Compute correctness labels using dual-signal approach.

    Label assignment: HIGH / MEDIUM / PRIORITY / DROP
    PRIORITY items (teacher strong but student disagrees) are high-value training
    signals where student is confidently wrong and teachers are confidently right —
    upweighted 3x in Ticket 6 trace selection.

    Returns:
        (labels_list, conflicts_list)
        labels_list: all items with label assignments
        conflicts_list: PRIORITY items where teacher != student (high-value training)
    """
    extractor = DataAppExtractor(strict_extract=False)
    labels = []
    conflicts = []
    per_teacher_accuracy = defaultdict(lambda: {"correct": 0, "total": 0})

    for manifest_entry in manifest:
        item_id = manifest_entry["id"]
        question_type = manifest_entry.get("question_type", "unknown")

        # 4-teacher consensus (3 from manifest + 1 from GPT-5.5)
        teacher_answers = {
            "sonnet": manifest_entry.get("sonnet_answer_raw", ""),
            "gpt5_4": manifest_entry.get("gpt5_4_answer_raw", ""),
            "gpt_oss": manifest_entry.get("gpt_oss_answer_raw", ""),
        }

        # Extract GPT-5.5 answer
        gpt55_response = load_gpt55_response(gpt55_dir, item_id)
        gpt55_answer = extract_gpt55_answer(gpt55_response, extractor)
        teacher_answers["gpt5_5"] = gpt55_answer

        consensus = compute_consensus(teacher_answers)
        consensus_answer = consensus["answer"]
        consensus_type = consensus["type"]

        # Student SC signal
        student_data = run14b.get(item_id)
        student_strong = student_data and student_data.get("agreement_rate", 0) >= 0.75
        student_answer = student_data.get("voted_answer", "") if student_strong else None

        # Label assignment logic
        teacher_strong = consensus_type in ["3/4", "4/4"]
        teacher_2of4 = consensus_type == "2/4"

        if teacher_strong and student_strong:
            if answers_match(consensus_answer, student_answer):
                label = "HIGH"
                rationale = "Teacher strong (>=3/4) AND student strong (>=0.75) AND answers match"
            else:
                label = "PRIORITY"
                rationale = "Teacher strong, student strong but disagrees — high-value training signal (student confidently wrong)"
                conflicts.append({
                    "item_id": item_id,
                    "question_type": question_type,
                    "teacher_answer": consensus_answer,
                    "teacher_agreement": consensus_type,
                    "student_answer": student_answer,
                    "student_agreement_rate": student_data.get("agreement_rate", 0),
                    "rationale": rationale,
                    "label": "PRIORITY",
                })
        elif teacher_strong and not student_strong:
            label = "MEDIUM"
            rationale = "Teacher strong (>=3/4), student not evaluated or weak"
        elif teacher_2of4 and student_strong:
            if answers_match(consensus_answer, student_answer):
                label = "MEDIUM"
                rationale = "Teacher split (2/4) but student strong (>=0.75) AND answers match"
            else:
                label = "DROP"
                rationale = "Conflict: teacher split and student disagree"
                conflicts.append({
                    "item_id": item_id,
                    "question_type": question_type,
                    "teacher_answer": consensus_answer,
                    "teacher_agreement": consensus_type,
                    "student_answer": student_answer,
                    "student_agreement_rate": student_data.get("agreement_rate", 0),
                    "rationale": rationale,
                })
        else:
            label = "DROP"
            rationale = "No strong consensus (teacher < 2/4 or no student support)"

        # Track per-teacher accuracy
        if label != "DROP":
            for teacher, answer in teacher_answers.items():
                if answer:
                    per_teacher_accuracy[teacher]["total"] += 1
                    if answers_match(answer, consensus_answer):
                        per_teacher_accuracy[teacher]["correct"] += 1

        labels.append({
            "id": item_id,
            "question_type": question_type,
            "label": label,
            "label_answer": consensus_answer,
            "rationale": rationale,
            "teacher_consensus": {
                "type": consensus_type,
                "which_agreed": consensus["which_agreed"],
                "answer": consensus_answer,
            },
            "teacher_answers": teacher_answers,
            "student_signal": {
                "answer": student_answer,
                "agreement_rate": student_data.get("agreement_rate") if student_data else None,
                "strong": student_strong,
            },
        })

    return labels, conflicts, per_teacher_accuracy


def main():
    """Build correctness labels."""
    logger.info("=== Building Correctness Labels ===")

    config = load_config()
    output_dir = Path(config["paths"]["output_dir"])
    manifest_path = output_dir / config["paths"]["manifest_file"]
    run14b_path = Path("/home/dvaneetv/private/151B_SP26_Competition/results/run14b_sc8_v1_private943_tok32k_pp1.jsonl")
    gpt55_dir = output_dir / "gpt55_full"

    # Verify inputs exist
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return 1

    if not gpt55_dir.exists():
        logger.error(f"GPT-5.5 responses not found: {gpt55_dir}")
        return 1

    # Load data
    manifest = read_jsonl(manifest_path)
    logger.info(f"Loaded {len(manifest)} items from manifest")

    run14b = load_run14b_data(run14b_path)

    # Compute labels
    labels, conflicts, teacher_acc = compute_labels(manifest, run14b, gpt55_dir, output_dir)

    # Summary stats
    label_dist = {"HIGH": 0, "MEDIUM": 0, "PRIORITY": 0, "DROP": 0}
    by_type = defaultdict(lambda: {"HIGH": 0, "MEDIUM": 0, "PRIORITY": 0, "DROP": 0})

    for label_entry in labels:
        label = label_entry["label"]
        label_dist[label] += 1
        by_type[label_entry["question_type"]][label] += 1

    # Save labels
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    labels_file = output_dir / f"correctness_labels_{timestamp}.json"
    with open(labels_file, "w") as f:
        json.dump(labels, f, indent=2)
    logger.info(f"Saved correctness labels: {labels_file}")

    # Save conflicts
    conflicts_file = output_dir / f"conflict_items_{timestamp}.json"
    with open(conflicts_file, "w") as f:
        json.dump(conflicts, f, indent=2)
    logger.info(f"Saved conflict items: {conflicts_file}")

    # Print summary
    print("\n" + "="*80)
    print("CORRECTNESS LABELS SUMMARY")
    print("="*80)
    print(f"\nLabel Distribution:")
    total = sum(label_dist.values())
    for label in ["HIGH", "MEDIUM", "PRIORITY", "DROP"]:
        count = label_dist[label]
        pct = 100 * count / max(total, 1)
        print(f"  {label}: {count:3d} items ({pct:5.1f}%)")

    print(f"\nBreakdown by Question Type:")
    for q_type in sorted(by_type.keys()):
        stats = by_type[q_type]
        total_type = sum(stats.values())
        print(f"  {q_type}:")
        for label in ["HIGH", "MEDIUM", "PRIORITY", "DROP"]:
            count = stats[label]
            pct = 100 * count / max(total_type, 1)
            print(f"    {label}: {count:3d} ({pct:5.1f}%)")

    print(f"\nConflict Items (teacher vs student disagreement): {len(conflicts)}")
    print(f"  {100*len(conflicts)/max(total,1):.1f}% of total")

    print(f"\nPer-Teacher Accuracy (on HIGH+MEDIUM items):")
    for teacher in sorted(teacher_acc.keys()):
        stats = teacher_acc[teacher]
        if stats["total"] > 0:
            acc = 100 * stats["correct"] / stats["total"]
            print(f"  {teacher}: {stats['correct']}/{stats['total']} ({acc:.1f}%)")

    print(f"\n{'='*80}")
    print(f"Outputs:")
    print(f"  Labels: {labels_file}")
    print(f"  Conflicts: {conflicts_file}")
    print("="*80 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
