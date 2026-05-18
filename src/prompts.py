"""
Locked prompts from DATAAPP_PROMPT_STRATEGY_LOCKED.md.
System prompt + type-specific suffixes for MCQ, single-answer, multi-answer.
"""

SYSTEM_PROMPT = """You are generating a math solution trace for supervised fine-tuning of a smaller reasoning model.

Your goal: produce a correct, clear, concise solution. Not flashy. Not verbose. Teachable.

Rules:
1. Show essential reasoning steps. Avoid unnecessary verification loops, restarts, or exploration of alternative paths.
2. Use exact symbolic form when natural (fractions, radicals, π). Use decimals only when the problem asks for them.
3. Do not use \\boxed{} anywhere except the final answer.
4. End with exactly one \\boxed{...} containing the final answer.
5. Briefly identify what is being asked before solving."""

SINGLE_ANSWER_SUFFIX = """Problem type: single-answer.

There is exactly one final answer. End with: \\boxed{answer}"""

MULTI_ANSWER_SUFFIX = """Problem type: multi-answer.

This problem requires multiple values. Before the final line, verify:
- you have produced exactly the required number of answers
- the order matches the problem's request
- the final answer uses exactly one \\boxed{...} with comma-separated values

End with: \\boxed{value1,value2,value3}"""

MCQ_SUFFIX = """Problem type: multiple choice.

Solve the problem and identify the correct option letter. End with: \\boxed{Letter}"""


def get_max_tokens(question_type: str) -> int:
    """
    Get differentiated token budget by question type.
    MCQ needs minimal reasoning (pick letter).
    Multi-free needs more (verify count + order).
    """
    return {"mcq": 2048, "single_free": 3584, "multi_free": 4608}[question_type]


def detect_question_type(item: dict) -> str:
    """
    Determine question type from item structure.

    Args:
        item: Item dict from private.jsonl

    Returns:
        "mcq", "single_free", or "multi_free"
    """
    # Check for MCQ (has options)
    if isinstance(item.get("options"), list) and len(item["options"]) > 0:
        return "mcq"

    # Check for multi-answer (multiple [ANS] placeholders)
    question = item.get("question", "")
    ans_count = question.count("[ANS]")
    if ans_count > 1:
        return "multi_free"

    # Single-answer (default)
    return "single_free"


def build_messages(question: str, question_type: str, options: list = None) -> list[dict]:
    """
    Build message list for API calls.

    Args:
        question: Question text from private.jsonl
        question_type: "mcq", "single_free", or "multi_free"
        options: List of option strings (for MCQ only)

    Returns:
        List of {"role": "system"|"user", "content": str} dicts
    """
    if question_type == "mcq":
        suffix = MCQ_SUFFIX
        if options:
            labels = [chr(65 + i) for i in range(len(options))]
            opts_text = "\n".join(f"{lbl}. {opt.strip()}" for lbl, opt in zip(labels, options))
            user_content = f"{question}\n\nOptions:\n{opts_text}\n\n{suffix}"
        else:
            user_content = f"{question}\n\n{suffix}"
    elif question_type == "multi_free":
        user_content = f"{question}\n\n{MULTI_ANSWER_SUFFIX}"
    else:  # single_free
        user_content = f"{question}\n\n{SINGLE_ANSWER_SUFFIX}"

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
