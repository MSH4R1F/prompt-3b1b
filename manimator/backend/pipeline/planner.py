import json
import pathlib

import anthropic

from pipeline.utils import strip_markdown_fences
from schemas.lesson import LessonPlan

_PROMPTS_DIR = pathlib.Path(__file__).parent.parent / "prompts"
_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text()


def plan_lesson(prompt: str, duration: int = 60, audience: str = "beginner") -> LessonPlan:
    client = _get_client()
    system = _load_prompt("planner_system.md")
    user_message = (
        f"Topic: {prompt}\n"
        f"Audience: {audience}\n"
        f"Duration: {duration} seconds\n\n"
        "Respond with ONLY valid JSON. No markdown fences."
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = strip_markdown_fences(response.content[0].text)
    data = json.loads(raw)
    return LessonPlan(**data)
