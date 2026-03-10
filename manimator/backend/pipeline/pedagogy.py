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

    raw = strip_markdown_fences(response.content[0].text)
    data = json.loads(raw)
    data.pop("approved", None)
    return LessonPlan(**data)
