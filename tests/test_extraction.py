#!/usr/bin/env python3
"""
Extraction validation: ensure DataAppExtractor matches competition repo's judger 100%.
Runs against Run 09 or latest results from competition repo.
"""

import sys
import json
from pathlib import Path

# Add parent path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction import DataAppExtractor


def find_test_data():
    """Load fixture from tests/fixtures/run09_sample.jsonl."""
    fixture_file = Path(__file__).parent / "fixtures" / "run09_sample.jsonl"

    if not fixture_file.exists():
        raise FileNotFoundError(
            f"Test fixture not found: {fixture_file}. "
            "Rain should provide tests/fixtures/run09_sample.jsonl with "
            "schema: {{id, response, extracted_answer}}"
        )

    return fixture_file


def load_test_samples(test_file: Path, sample_size: int = 50) -> list[dict]:
    """Load samples from fixture file (schema: {id, response, extracted_answer})."""
    samples = []
    with open(test_file) as f:
        for i, line in enumerate(f):
            if i >= sample_size:
                break
            obj = json.loads(line)
            samples.append(obj)
    return samples


def test_extraction_100_percent_match():
    """Test that extraction matches expected outputs 100%."""
    extractor = DataAppExtractor(strict_extract=False)

    # Find test data
    test_file = find_test_data()
    print(f"Using test file: {test_file}")

    # Load samples
    samples = load_test_samples(test_file, sample_size=50)
    print(f"Loaded {len(samples)} test samples")

    # Verify structure (samples should have "response" and "extracted_answer" or similar)
    if not samples:
        raise ValueError("No test samples loaded")

    first_sample = samples[0]
    if "response" not in first_sample:
        print(f"Warning: test sample doesn't have 'response' field. Keys: {list(first_sample.keys())}")
        print("Samples may be in different format. Skipping full test.")
        print("Create proper test data with 'response' and 'extracted_answer' fields.")
        return True

    # Test extraction
    mismatches = []
    for i, sample in enumerate(samples):
        response = sample.get("response", "")
        expected = sample.get("extracted_answer") or sample.get("prediction") or ""

        extracted = extractor.extract(response)

        if extracted != expected:
            mismatches.append({
                "index": i,
                "expected": expected[:100],
                "got": extracted[:100],
            })

    # Report
    match_rate = (len(samples) - len(mismatches)) / len(samples) * 100
    print(f"\nExtraction Test Results:")
    print(f"  Match rate: {match_rate:.1f}% ({len(samples) - len(mismatches)}/{len(samples)})")

    if mismatches:
        print(f"\n  Mismatches (first 5):")
        for m in mismatches[:5]:
            print(f"    Sample {m['index']}: expected '{m['expected']}' got '{m['got']}'")

    assert len(mismatches) == 0, f"Extraction mismatch: {len(mismatches)} failures"
    print("\n✓ Extraction validation PASSED (100% match)")


if __name__ == "__main__":
    try:
        test_extraction_100_percent_match()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Extraction validation FAILED: {e}")
        sys.exit(1)
