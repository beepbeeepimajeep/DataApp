"""
Prompts for DataApp LLM queries. Same prompt for all 3 models (Anthropic, OpenAI, Moonshot).
"""

SYSTEM_PROMPT = """You are a math problem solver specialized in competition-level mathematics (AMC, AIME, IMO style).

Your task: solve the given problem and provide your final answer in a \\boxed{} block.

Rules:
- Show your work/reasoning.
- For single-answer problems: \\boxed{your_answer}
- For multi-answer problems: \\boxed{answer1, answer2, ...} (comma-separated, no spaces after commas)
- Always use \\boxed{} for the final answer, even if uncertain.
- For multiple answers, order them as requested in the problem.
"""


def get_user_prompt(problem: str) -> str:
    """Format problem as user message."""
    return f"""Solve this problem:

{problem}"""


def get_conversation(problem: str) -> list[dict]:
    """Return conversation list for API calls.

    Args:
        problem: The problem text to solve.

    Returns:
        List of dicts: [{"role": "user", "content": "..."}]
    """
    return [{"role": "user", "content": get_user_prompt(problem)}]
