from pydantic import BaseModel, Field


class Segment(BaseModel):
    narration: str
    visual_intent: list[str]
    text_classes: dict[str, str]
    positions: dict[str, str]
    suggested_helpers: list[str] = Field(default_factory=list)


class LessonPlan(BaseModel):
    topic: str
    audience: str
    duration: int
    segments: list[Segment]
