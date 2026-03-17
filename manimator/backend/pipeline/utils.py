"""Shared utilities for pipeline modules."""


def strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences from LLM output.

    Handles:
    - No fences (returns text unchanged)
    - ```json ... ``` (removes opening language-tagged fence and closing fence)
    - ``` ... ``` (removes plain fences)
    - Trailing text after the closing fence is discarded
    """
    text = text.strip()
    if not text.startswith("```"):
        return text

    # Remove the opening fence line (e.g. "```json" or "```")
    first_newline = text.find("\n")
    if first_newline == -1:
        return ""
    text = text[first_newline + 1:]

    # Remove everything from the first closing fence onwards
    closing = text.find("```")
    if closing != -1:
        text = text[:closing]

    return text.strip()
