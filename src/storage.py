"""
Atomic JSON write/read operations for DataApp outputs.
Uses temp file + rename to ensure atomicity.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Optional


def atomic_write_json(data: dict, filepath: Path) -> None:
    """
    Write JSON atomically (temp file + rename).

    Args:
        data: Dictionary to write.
        filepath: Target file path.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first
    with tempfile.NamedTemporaryFile(
        mode="w", dir=filepath.parent, delete=False, suffix=".json"
    ) as tmp:
        json.dump(data, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic rename
    Path(tmp_path).rename(filepath)


def read_json(filepath: Path) -> Optional[dict]:
    """
    Read JSON file safely.

    Args:
        filepath: File to read.

    Returns:
        Parsed dict, or None if file doesn't exist.
    """
    if not filepath.exists():
        return None
    try:
        with open(filepath) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {filepath}: {e}")
        return None


def append_jsonl(data: dict, filepath: Path) -> None:
    """
    Append one JSON object per line (JSONL format).

    Args:
        data: Dictionary to append.
        filepath: Target file path.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "a") as f:
        json.dump(data, f)
        f.write("\n")


def read_jsonl(filepath: Path) -> list[dict]:
    """
    Read JSONL file (one JSON object per line).

    Args:
        filepath: File to read.

    Returns:
        List of parsed dicts.
    """
    if not filepath.exists():
        return []

    items = []
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading {filepath}: {e}")

    return items


def get_completed_ids(filepath: Path) -> set[int]:
    """
    Get set of completed item IDs from JSONL manifest.

    Args:
        filepath: Path to manifest JSONL file.

    Returns:
        Set of completed item IDs.
    """
    items = read_jsonl(filepath)
    return {item.get("id") for item in items if "id" in item}
