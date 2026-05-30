#!/usr/bin/env python3
"""Export compact GPT-5.5 xhigh teacher answers to a CSV."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.extraction import extract_boxed_answer, normalize_answer


RESPONSE_DIR = REPO_ROOT / "dataapp_outputs" / "gpt55_full"
RECOVERY_PATH = REPO_ROOT / "data" / "xhigh_refusal_recovery.json"
OUTPUT_PATH = REPO_ROOT / "data" / "teacher_xhigh_answers.csv"

EXPECTED_ROWS = 943

REFUSAL_MARKERS = (
    "i'm sorry",
    "i am sorry",
    "sorry, but",
    "sorry but",
    "i can't",
    "i cannot",
    "cannot help",
    "can't help",
    "cannot provide",
    "can't provide",
    "unable to help",
    "unable to provide",
    "cannot comply",
    "can't comply",
    "refuse",
    "decline",
)

RECOVERABLE_PLACEHOLDERS = (
    "no correct option",
    "none of the listed options",
    "none of the above",
    "none of a--j",
    "no listed option",
    "cannot be determined from the provided information",
    "cannot be determined",
    "no such cube exists",
)


def load_recoveries() -> dict[str, str]:
    with RECOVERY_PATH.open() as handle:
        payload = json.load(handle)
    return {str(key): value for key, value in payload.get("integrate", {}).items()}


def load_response_body(path: Path) -> str:
    text = path.read_text()
    if "## Reasoning + Response" in text:
        text = text.split("## Reasoning + Response", 1)[1]
    if "\n## Metadata" in text:
        text = text.split("\n## Metadata", 1)[0]
    return text.strip()


def classify_no_box(response_body: str) -> str:
    compact = re.sub(r"\s+", " ", response_body).strip().lower()
    if any(marker in compact for marker in REFUSAL_MARKERS):
        return "refusal"
    return "no_box"


def is_recoverable_placeholder(answer: str) -> bool:
    normalized = normalize_answer(answer).strip().lower()
    return any(normalized.startswith(prefix) for prefix in RECOVERABLE_PLACEHOLDERS)


def build_rows() -> tuple[list[dict[str, str]], Counter, list[str], list[tuple[str, str, str]]]:
    recoveries = load_recoveries()
    rows: list[dict[str, str]] = []
    status_counts: Counter = Counter()
    failed_items: list[str] = []
    verification_checks: list[tuple[str, str, str]] = []

    for item_id in range(EXPECTED_ROWS):
        item_key = str(item_id)
        response_path = RESPONSE_DIR / f"item_{item_id:04d}_gpt5_5_response.md"
        response_body = load_response_body(response_path)
        extracted = extract_boxed_answer(response_body).strip()

        if extracted:
            if item_key in recoveries and is_recoverable_placeholder(extracted):
                answer = recoveries[item_key]
                status = "recovered"
            else:
                answer = extracted
                status = "ok"
        else:
            status = classify_no_box(response_body)
            if status == "refusal" and item_key in recoveries:
                answer = recoveries[item_key]
                status = "recovered"
            else:
                answer = ""

        row = {
            "item_id": item_key,
            "xhigh_answer": answer,
            "status": status,
        }
        rows.append(row)
        status_counts[status] += 1

        if status in {"refusal", "no_box"}:
            failed_items.append(item_key)

        if status == "ok" and len(verification_checks) < 5:
            verification_checks.append((item_key, extracted, answer))

    return rows, status_counts, failed_items, verification_checks


def write_csv(rows: list[dict[str, str]]) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["item_id", "xhigh_answer", "status"])
        writer.writeheader()
        writer.writerows(rows)


def verify(rows: list[dict[str, str]], checks: list[tuple[str, str, str]]) -> None:
    if len(rows) != EXPECTED_ROWS:
        raise RuntimeError(f"Expected {EXPECTED_ROWS} rows, found {len(rows)}")

    item_zero = rows[0]
    if item_zero["item_id"] != "0":
        raise RuntimeError(f"item_0000 mapped to {item_zero['item_id']} instead of 0")

    for item_id, extracted, csv_answer in checks:
        if extracted != csv_answer:
            raise RuntimeError(
                f"Spot check mismatch for item {item_id}: extracted={extracted!r}, csv={csv_answer!r}"
            )


def main() -> None:
    rows, status_counts, failed_items, checks = build_rows()
    write_csv(rows)
    verify(rows, checks)

    item_zero = rows[0]
    print(f"Wrote {len(rows)} rows to {OUTPUT_PATH}")
    print("Status histogram:")
    for status in ("ok", "recovered", "refusal", "no_box"):
        print(f"  {status}: {status_counts.get(status, 0)}")

    print("Spot checks (file last \\boxed{} vs CSV):")
    for item_id, extracted, csv_answer in checks:
        print(f"  item_{int(item_id):04d}: {extracted!r} == {csv_answer!r}")

    print(
        "item_0000 check: "
        f"id={item_zero['item_id']!r}, answer={item_zero['xhigh_answer']!r}, status={item_zero['status']!r}"
    )

    if failed_items:
        print("Failed extraction items:")
        print("  " + ", ".join(failed_items))
    else:
        print("Failed extraction items: none")


if __name__ == "__main__":
    main()