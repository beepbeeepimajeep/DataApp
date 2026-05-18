"""
Main orchestrator for DataApp execution.
Handles parallel API calls, extraction, voting, and resume logic.
"""

import json
import logging
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

from .api_clients import AnthropicClient, OpenAIClient, MoonshotClient
from .extraction import DataAppExtractor
from .storage import (
    atomic_write_json,
    read_json,
    append_jsonl,
    read_jsonl,
    get_completed_ids,
)
from .cost_tracker import CostTracker
from .prompts import get_conversation, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class DataAppOrchestrator:
    """Orchestrate DataApp pipeline execution."""

    def __init__(self, config: dict):
        """
        Initialize orchestrator.

        Args:
            config: Configuration dict (from config.yaml).
        """
        self.config = config
        self.data_dir = Path(config["paths"]["data_dir"])
        self.output_dir = Path(config["paths"]["output_dir"])
        self.manifest_file = self.output_dir / config["paths"]["manifest_file"]

        # Initialize API clients
        models_config = config.get("models", {})
        self.anthropic = AnthropicClient(
            config=models_config.get("anthropic", {})
        )
        self.openai = OpenAIClient(config=models_config.get("openai", {}))
        self.moonshot = MoonshotClient(config=models_config.get("moonshot", {}))

        # Initialize extractor
        self.extractor = DataAppExtractor(strict_extract=False)

        # Cost tracking
        self.cost_tracker = CostTracker()

        # Execution config
        exec_config = config.get("execution", {})
        self.max_retries = exec_config.get("max_retries", 3)
        self.retry_backoff = exec_config.get("retry_backoff_seconds", 2.0)

    def query_all_models(self, item_id: int, problem: str) -> dict:
        """
        Query all 3 models in parallel.

        Args:
            item_id: Item ID for output tracking.
            problem: Problem text.

        Returns:
            Dict with keys: "anthropic", "openai", "moonshot" (each is full response dict).
        """
        messages = get_conversation(problem)
        responses = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self.anthropic.query,
                    messages,
                    self.max_retries,
                    self.retry_backoff,
                ): "anthropic",
                executor.submit(
                    self.openai.query,
                    messages,
                    self.max_retries,
                    self.retry_backoff,
                ): "openai",
                executor.submit(
                    self.moonshot.query,
                    messages,
                    self.max_retries,
                    self.retry_backoff,
                ): "moonshot",
            }

            for future in as_completed(futures):
                vendor = futures[future]
                try:
                    result = future.result()
                    responses[vendor] = result
                    self.cost_tracker.add_call(
                        vendor,
                        result["input_tokens"],
                        result["output_tokens"],
                        result["cost_usd"],
                    )
                    logger.info(
                        f"Item {item_id} {vendor}: "
                        f"{result['input_tokens']} in, "
                        f"{result['output_tokens']} out, "
                        f"${result['cost_usd']:.4f}"
                    )
                except Exception as e:
                    logger.error(f"Item {item_id} {vendor} failed: {e}")
                    responses[vendor] = None

        return responses

    def extract_answers(self, responses: dict) -> dict:
        """
        Extract answers from all 3 model responses.

        Args:
            responses: Dict with "anthropic", "openai", "moonshot" responses.

        Returns:
            Dict with extracted answers.
        """
        extracted = {}
        for vendor, result in responses.items():
            if result and "response" in result:
                extracted[vendor] = self.extractor.extract(result["response"])
            else:
                extracted[vendor] = ""

        return extracted

    def vote_on_answer(self, extracted: dict) -> tuple[str, int, bool]:
        """
        Vote on best answer (majority vote, lexicographic tie-break).

        Args:
            extracted: Dict with extracted answers from each model.

        Returns:
            Tuple: (consensus_answer, vote_count, is_tie_broken)
        """
        candidates = [v for v in extracted.values() if v]
        if not candidates:
            return ("", 0, False)

        votes = Counter(candidates)
        if not votes:
            return ("", 0, False)

        # Get most common answer
        most_common, count = votes.most_common(1)[0]

        # Check if tie
        top_candidates = [ans for ans, c in votes.items() if c == count]
        is_tie = len(top_candidates) > 1

        if is_tie:
            # Lexicographic tie-break
            consensus = sorted(top_candidates)[0]
        else:
            consensus = most_common

        return (consensus, count, is_tie)

    def compute_agreement_rate(self, extracted: dict) -> float:
        """
        Compute agreement rate (fraction of models agreeing with consensus).

        Args:
            extracted: Dict with extracted answers from each model.

        Returns:
            Agreement rate (0.0 to 1.0).
        """
        if not extracted or not any(extracted.values()):
            return 0.0

        consensus, count, _ = self.vote_on_answer(extracted)
        if not consensus:
            return 0.0

        return count / len([v for v in extracted.values() if v])

    def process_item(self, item: dict) -> dict:
        """
        Process one item: query, extract, vote, save.

        Args:
            item: Item dict from private.jsonl (must have "id" and problem field).

        Returns:
            Manifest entry dict.
        """
        item_id = item.get("id")
        problem = item.get("problem", "")

        logger.info(f"Processing item {item_id}...")

        # Query all models
        responses = self.query_all_models(item_id, problem)

        # Extract answers
        extracted = self.extract_answers(responses)

        # Vote on consensus
        consensus, vote_count, is_tie = self.vote_on_answer(extracted)

        # Compute agreement rate
        agreement_rate = self.compute_agreement_rate(extracted)

        # Save item outputs
        item_dir = self.output_dir / f"item_{item_id}"
        item_dir.mkdir(parents=True, exist_ok=True)

        # Save individual responses
        for vendor, result in responses.items():
            if result:
                atomic_write_json(result, item_dir / f"{vendor}.json")
            else:
                atomic_write_json({"error": "Query failed"}, item_dir / f"{vendor}.json")

        # Save extraction
        atomic_write_json(extracted, item_dir / "extraction.json")

        # Save manifest entry
        manifest_entry = {
            "id": item_id,
            "type": item.get("type", "unknown"),
            "extracted": extracted,
            "consensus": consensus,
            "vote_count": vote_count,
            "is_tie": is_tie,
            "agreement_rate": agreement_rate,
            "cost_usd": sum(
                r["cost_usd"] for r in responses.values() if r and "cost_usd" in r
            ),
        }
        atomic_write_json(manifest_entry, item_dir / "manifest.json")

        # Append to global manifest
        append_jsonl(manifest_entry, self.manifest_file)

        return manifest_entry

    def get_completed_ids(self) -> set[int]:
        """Get set of already-completed item IDs."""
        return get_completed_ids(self.manifest_file)

    def get_items_to_process(
        self, items: list[dict], skip_completed: bool = True
    ) -> list[dict]:
        """
        Filter items, optionally skipping completed ones.

        Args:
            items: List of items from private.jsonl.
            skip_completed: If True, skip already-completed IDs.

        Returns:
            Filtered list of items.
        """
        if not skip_completed:
            return items

        completed = self.get_completed_ids()
        return [item for item in items if item.get("id") not in completed]

    def run_batch(self, items: list[dict]) -> dict:
        """
        Process a batch of items.

        Args:
            items: List of items to process.

        Returns:
            Summary dict with stats.
        """
        processed = 0
        failed = 0
        total_cost = 0.0
        total_agreement = 0.0

        for item in items:
            try:
                entry = self.process_item(item)
                processed += 1
                total_cost += entry.get("cost_usd", 0)
                total_agreement += entry.get("agreement_rate", 0)
            except Exception as e:
                logger.error(f"Item {item.get('id')} failed: {e}")
                failed += 1

        avg_agreement = total_agreement / max(processed, 1)

        return {
            "processed": processed,
            "failed": failed,
            "total_cost_usd": total_cost,
            "avg_agreement_rate": avg_agreement,
            "cost_summary": self.cost_tracker.summary(),
        }
