"""
Atomic JSON write/read operations for DataApp outputs.
Uses temp file + rename to ensure atomicity.
Provides utility functions and a Storage class for managing item outputs.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timezone


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


def _atomic_write(path: Path, content: str) -> None:
    """
    Write to temp file then rename (atomic).

    Args:
        path: Target file path
        content: Content to write
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())
    os.rename(tmp, path)


class Storage:
    """Manages per-item output files and manifest for DataApp."""

    def __init__(self, output_dir: str, manifest_path: str):
        """
        Initialize storage.

        Args:
            output_dir: Directory for item_XXXX/ subdirs
            manifest_path: Path to dataset_manifest.jsonl
        """
        self.output_dir = Path(output_dir)
        self.manifest_path = Path(manifest_path)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)

    def item_dir(self, item_id: int) -> Path:
        """Get or create directory for a specific item."""
        d = self.output_dir / f"item_{int(item_id):04d}"
        d.mkdir(exist_ok=True)
        return d

    def save_response(
        self, item_id: int, teacher_key: str, response_data: dict, prompt: str
    ) -> None:
        """
        Save teacher response atomically as .md and .json.

        Args:
            item_id: Item ID
            teacher_key: "sonnet", "gpt5_4", or "gpt_oss"
            response_data: Dict with response, tokens, model, etc.
            prompt: The prompt sent to the teacher
        """
        d = self.item_dir(item_id)

        # Save markdown response
        md_path = d / f"{teacher_key}_response.md"
        md_content = self._format_response_md(response_data, prompt, teacher_key)
        _atomic_write(md_path, md_content)

        # Save metadata JSON
        meta_path = d / f"{teacher_key}_metadata.json"
        meta = {
            "teacher": teacher_key,
            "model": response_data.get("model", ""),
            "input_tokens": response_data.get("input_tokens", 0),
            "output_tokens": response_data.get("output_tokens", 0),
            "hit_token_cap": response_data.get("hit_token_cap", False),
            "finish_reason": response_data.get("finish_reason"),
            "generation_time_s": response_data.get("generation_time_s", 0),
            "request_id": response_data.get("request_id"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": response_data.get("error"),
        }
        _atomic_write(meta_path, json.dumps(meta, indent=2))

    def save_extraction(
        self, item_id: int, teacher_key: str, extracted: str, has_boxed: bool, n_boxes: int
    ) -> None:
        """
        Save extraction result to extractions.json.

        Args:
            item_id: Item ID
            teacher_key: Teacher key
            extracted: Extracted answer string
            has_boxed: Whether response contained \\boxed{}
            n_boxes: Count of \\boxed{} blocks
        """
        d = self.item_dir(item_id)
        ext_path = d / "extractions.json"

        existing = {}
        if ext_path.exists():
            try:
                with open(ext_path) as f:
                    existing = json.load(f)
            except:
                existing = {}

        existing[teacher_key] = {
            "extracted_answer": extracted,
            "has_boxed": has_boxed,
            "n_boxes": n_boxes,
        }
        _atomic_write(ext_path, json.dumps(existing, indent=2))

    def append_manifest(self, manifest_entry: dict) -> None:
        """Append one entry to manifest.jsonl."""
        with open(self.manifest_path, "a") as f:
            f.write(json.dumps(manifest_entry) + "\n")

    def completed_items(self) -> set[int]:
        """Get set of completed item IDs from manifest."""
        return get_completed_ids(self.manifest_path)

    def _format_response_md(self, response_data: dict, prompt: str, teacher_key: str) -> str:
        """Format response as markdown with metadata footer."""
        error_note = f"\n\n**ERROR:** {response_data.get('error')}" if response_data.get("error") else ""
        return f"""# {teacher_key} Response

## Prompt
```
{prompt}
```

## Reasoning + Response
{response_data.get('response', '')}

## Metadata
- Model: {response_data.get('model', '')}
- Input tokens: {response_data.get('input_tokens', 0)}
- Output tokens: {response_data.get('output_tokens', 0)}
- Hit token cap: {response_data.get('hit_token_cap', False)}
- Generation time: {response_data.get('generation_time_s', 0):.2f}s
- Request ID: {response_data.get('request_id', 'N/A')}{error_note}
"""
