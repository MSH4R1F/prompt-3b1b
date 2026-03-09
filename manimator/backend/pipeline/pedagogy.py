import json
import pathlib
from typing import Optional

import anthropic

from schemas.lesson import LessonPlan

_PROMPTS_DIR = pathlib.Path(__file__).parent.parent / "prompts"
_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n", 1)
        text = lines[1] if len(lines) > 1 else ""
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def pedagogy_check(plan: LessonPlan) -> LessonPlan:
    client = _get_client()
    system_template = (_PROMPTS_DIR / "pedagogy_system.md").read_text()
    system = system_template.replace("{duration}", str(plan.duration)).replace("{audience}", plan.audience)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system,
        messages=[
            {
                "role": "user",
                "content": plan.model_dump_json(indent=2) + "\nReturn ONLY valid JSON.",
            }
        ],
    )

    raw = _strip_markdown_fences(response.content[0].text)
    data = json.loads(raw)
    data.pop("approved", None)
    return LessonPlan(**data)
