"""
Main orchestration: load items, dispatch to 3 teachers, compute consensus.
Resume-safe: skips already-completed items.
"""

import json
import logging
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from .api_clients import SonnetClient, GPT54Client, GPTOSSClient
from .extraction import DataAppExtractor
from .prompts import build_messages, detect_question_type
from .storage import Storage
from .cost_tracker import CostTracker

logger = logging.getLogger(__name__)

REASONING_KEYWORDS = {
    "Derivation", "Deriv", "Step", "Therefore", "Thus", "Hence", "So",
    "Conclude", "Result", "Answer", "Solve", "Simplify", "Expand", "Factor",
    "Rearrange", "Substitute", "Equation", "Expression", "Formula", "Calculate"
}


def has_reasoning(response: str) -> bool:
    """
    Heuristic check for reasoning presence in response.
    Returns True if response >100 chars AND contains reasoning keywords.
    """
    if not response or len(response) < 100:
        return False

    response_lower = response.lower()
    return any(keyword.lower() in response_lower for keyword in REASONING_KEYWORDS)


def load_items(jsonl_path: str) -> list[dict]:
    """Load all items from private.jsonl."""
    items = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
    except Exception as e:
        logger.error(f"Error loading items: {e}")
        raise
    return items


def compute_consensus(extractions: dict) -> dict:
    """
    Compute agreement type using normalized comparison for cross-teacher matching.

    Parametric over N teachers. Agreement type is reported as 'N/M' where M is
    the number of non-empty teacher extractions and N is the size of the largest
    agreement group. Backward-compatible with prior 3-teacher use.

    Args:
        extractions: {teacher_key: extracted_answer, ...}

    Returns:
        {
            "type": "N/M" (e.g. "4/4", "3/4", "2/3", "1/4", "0/0"),
            "which_agreed": [teacher_keys] (members of largest agreement group),
            "answer": consensus_answer (RAW, from first teacher in largest group)
        }
    """
    from .consensus_normalizer import answers_match

    # Exclude empty extractions
    valid = {t: a for t, a in extractions.items() if a}

    if not valid:
        return {"type": "0/0", "which_agreed": [], "answer": ""}

    teachers = list(valid.keys())
    answers = list(valid.values())

    # Build agreement groups using pairwise normalized matching
    groups = []
    assigned = set()
    for i, t in enumerate(teachers):
        if t in assigned:
            continue
        group = [t]
        assigned.add(t)
        for j in range(i + 1, len(teachers)):
            if teachers[j] not in assigned:
                if answers_match(answers[i], answers[j]):
                    group.append(teachers[j])
                    assigned.add(teachers[j])
        groups.append(group)

    # Find largest group
    largest = max(groups, key=len)
    count = len(largest)
    total = len(valid)

    # Parametric agreement type: N/M where N is agreement count, M is total valid teachers
    type_str = f"{count}/{total}"

    # Use RAW answer from first teacher in largest group
    consensus_answer = valid[largest[0]]

    return {
        "type": type_str,
        "which_agreed": largest,
        "answer": consensus_answer,
    }


class DataAppOrchestrator:
    """Orchestrate DataApp pipeline execution."""

    def __init__(self, config: dict):
        """Initialize orchestrator from config."""
        self.config = config

        # Initialize storage
        output_dir = config["paths"]["output_dir"]
        manifest_file = config["paths"]["manifest_file"]
        manifest_path = str(Path(output_dir) / manifest_file)
        self.storage = Storage(output_dir, manifest_path)

        # Initialize API clients (new 3-teacher lineup)
        self.gpt5_4 = GPT54Client(tritonai_model="gpt-5.4", openai_model="gpt-5.4")
        self.gpt_oss = GPTOSSClient(model="api-gpt-oss-120b")
        self.sonnet = SonnetClient(model="claude-sonnet-4-6")
        self.clients = {"gpt5_4": self.gpt5_4, "gpt_oss": self.gpt_oss, "sonnet": self.sonnet}
        self.teacher_keys = ["gpt5_4", "gpt_oss", "sonnet"]

        # Initialize extractor
        self.extractor = DataAppExtractor(strict_extract=False)

        # Initialize cost tracker
        cost_log = str(Path(output_dir) / "cost_log.jsonl")
        alert_thresholds = config.get("cost_tracking", {}).get("alert_thresholds", [])
        self.cost_tracker = CostTracker(cost_log, alert_thresholds)

    def _load_cached_response(self, item_id: int, teacher: str) -> dict | None:
        """Load cached response if it exists, otherwise return None."""
        response_file = self.storage.item_dir(item_id) / f"{teacher}_response.md"
        metadata_file = self.storage.item_dir(item_id) / f"{teacher}_metadata.json"

        if response_file.exists() and metadata_file.exists():
            try:
                with open(response_file) as f:
                    response_text = f.read()
                with open(metadata_file) as f:
                    metadata = json.load(f)
                # Reconstruct result dict
                return {
                    "response": response_text,
                    "input_tokens": metadata.get("input_tokens", 0),
                    "output_tokens": metadata.get("output_tokens", 0),
                    "hit_token_cap": metadata.get("hit_token_cap", False),
                    "generation_time_s": metadata.get("generation_time_s", 0),
                    "model": metadata.get("model", ""),
                    "request_id": metadata.get("request_id"),
                    "error": None,
                    "route": metadata.get("route", "cached"),
                }
            except Exception as e:
                logger.warning(f"Failed to load cached {teacher} response for item {item_id}: {e}")
                return None
        return None

    def run_item(self, item: dict) -> dict:
        """
        Process one item through all 3 teachers and compute consensus.

        Args:
            item: Item dict from private.jsonl

        Returns:
            Manifest entry dict
        """
        item_id = item["id"]
        question = item.get("question", "")
        options = item.get("options")

        question_type = detect_question_type(item)
        messages = build_messages(question, question_type, options)
        max_tokens = 16384  # Uniform budget for all question types

        # Prompt for logging
        prompt_for_log = messages[-1]["content"]

        logger.info(f"Processing item {item_id} ({question_type}, max_tokens={max_tokens})...")

        # Query 3 teachers in parallel (skip cached responses)
        results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}

            # Check for cached Sonnet response
            cached = self._load_cached_response(item_id, "sonnet")
            if cached:
                results["sonnet"] = cached
                logger.info(f"  → using cached sonnet response")
            else:
                futures[executor.submit(self.sonnet.call, messages, 0.6, max_tokens)] = "sonnet"

            # Always query gpt5_4 and gpt_oss (they're new)
            futures[executor.submit(self.gpt5_4.call, messages, 0.6, max_tokens)] = "gpt5_4"
            futures[executor.submit(self.gpt_oss.call, messages, 0.6, max_tokens)] = "gpt_oss"

            for fut in as_completed(futures):
                teacher = futures[fut]
                try:
                    results[teacher] = fut.result()
                except Exception as e:
                    logger.error(f"Item {item_id} {teacher} failed: {e}")
                    results[teacher] = {
                        "response": "",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "error": str(e),
                        "hit_token_cap": False,
                        "generation_time_s": 0,
                        "model": self.clients[teacher].model,
                        "request_id": None,
                    }

        # Save responses + metadata, extract answers, track cost
        extractions = {}
        for teacher in self.teacher_keys:
            r = results[teacher]
            self.storage.save_response(item_id, teacher, r, prompt_for_log)

            # Track cost (include route for GPT-5.4 fallback tracking)
            if not r.get("error"):
                self.cost_tracker.record(
                    item_id, r["model"], r["input_tokens"], r["output_tokens"], r.get("route")
                )

            # Extract answer
            extracted = self.extractor.extract(r["response"]) if r.get("response") else ""
            has_boxed = self.extractor.has_boxed(r["response"]) if r.get("response") else False
            n_boxes = self.extractor.count_boxed(r["response"]) if r.get("response") else 0

            extractions[teacher] = extracted
            self.storage.save_extraction(item_id, teacher, extracted, has_boxed, n_boxes)

        # Compute consensus
        consensus = compute_consensus(extractions)

        # Check for reasoning presence in each model's response
        reasoning_present = {}
        for teacher in self.teacher_keys:
            response = results[teacher].get("response", "")
            reasoning_present[teacher] = has_reasoning(response)

        # Check if any model hit token cap
        any_hit_cap = any(results[t].get("hit_token_cap", False) for t in self.teacher_keys)

        # Build per-model metadata for new teachers
        gpt5_4_meta = {
            "input_tokens": results["gpt5_4"].get("input_tokens", 0),
            "output_tokens": results["gpt5_4"].get("output_tokens", 0),
            "hit_token_cap": results["gpt5_4"].get("hit_token_cap", False),
            "generation_time_s": results["gpt5_4"].get("generation_time_s", 0),
        }
        gpt_oss_meta = {
            "input_tokens": results["gpt_oss"].get("input_tokens", 0),
            "output_tokens": results["gpt_oss"].get("output_tokens", 0),
            "hit_token_cap": results["gpt_oss"].get("hit_token_cap", False),
            "generation_time_s": results["gpt_oss"].get("generation_time_s", 0),
        }
        sonnet_meta = {
            "input_tokens": results["sonnet"].get("input_tokens", 0),
            "output_tokens": results["sonnet"].get("output_tokens", 0),
            "hit_token_cap": results["sonnet"].get("hit_token_cap", False),
            "generation_time_s": results["sonnet"].get("generation_time_s", 0),
        }

        # Build manifest entry with both raw and consensus answers
        manifest_entry = {
            "id": item_id,
            "question_type": question_type,
            "gpt5_4_answer_raw": extractions.get("gpt5_4", ""),
            "gpt_oss_answer_raw": extractions.get("gpt_oss", ""),
            "sonnet_answer_raw": extractions.get("sonnet", ""),
            "agreement_type": consensus["type"],
            "which_agreed": consensus["which_agreed"],
            "consensus_answer": consensus["answer"],
            "any_errors": any(results[t].get("error") for t in self.teacher_keys),
            "reasoning_present": reasoning_present,
            "gpt5_4_metadata": gpt5_4_meta,
            "gpt_oss_metadata": gpt_oss_meta,
            "sonnet_metadata": sonnet_meta,
            "route_gpt5_4": results["gpt5_4"].get("route", "tritonai"),
            "any_hit_cap": any_hit_cap,
        }

        self.storage.append_manifest(manifest_entry)

        logger.info(
            f"  → {manifest_entry['agreement_type']} "
            f"(consensus: {manifest_entry['consensus_answer'][:50] if manifest_entry['consensus_answer'] else 'NONE'})"
        )
        logger.info(f"  → running cost: ${self.cost_tracker.total_cost_usd():.2f}")

        return manifest_entry

    def get_completed_ids(self) -> set[int]:
        """Get set of already-completed item IDs."""
        return self.storage.completed_items()

    def run_batch(self, items: list[dict], skip_completed: bool = True) -> dict:
        """
        Process a batch of items.

        Args:
            items: List of items to process
            skip_completed: If True, skip already-done items

        Returns:
            Summary dict with stats
        """
        if skip_completed:
            completed = self.get_completed_ids()
            items = [i for i in items if i["id"] not in completed]

        logger.info(f"Processing {len(items)} items...")

        processed = 0
        failed = 0

        for item in items:
            try:
                self.run_item(item)
                processed += 1
            except Exception as e:
                logger.error(f"Item {item.get('id')} failed: {e}")
                failed += 1

        return {
            "processed": processed,
            "failed": failed,
            "total_cost_usd": self.cost_tracker.total_cost_usd(),
        }
