"""Tests for Pydantic schemas."""

from schemas.job import Job, JobStatus
from schemas.lesson import LessonPlan, Segment


def test_lesson_plan_valid():
    data = {
        "topic": "binary search",
        "audience": "beginner",
        "duration": 60,
        "segments": [
            {
                "narration": "Imagine a sorted list.",
                "visual_intent": ["number_line", "dot"],
                "text_classes": {"title": "Text"},
                "positions": {"title": "top"},
                "suggested_helpers": ["safe_text"],
            }
        ],
    }
    plan = LessonPlan(**data)
    assert plan.topic == "binary search"
    assert len(plan.segments) == 1


def test_lesson_plan_multiple_segments():
    plan = LessonPlan(
        topic="addition",
        audience="beginner",
        duration=45,
        segments=[
            Segment(
                narration="seg 1",
                visual_intent=["text"],
                text_classes={"title": "Text"},
                positions={"title": "top"},
            ),
            Segment(
                narration="seg 2",
                visual_intent=["formula"],
                text_classes={"eq": "MathTex"},
                positions={"eq": "center"},
            ),
        ],
    )
    assert len(plan.segments) == 2
    assert plan.segments[1].text_classes["eq"] == "MathTex"


def test_segment_defaults():
    seg = Segment(narration="test", visual_intent=["dot"], text_classes={}, positions={})
    assert seg.suggested_helpers == []


def test_job_status_enum():
    assert JobStatus.PROCESSING == "processing"
    assert JobStatus.COMPLETED == "completed"
    assert JobStatus.FAILED == "failed"


def test_job_valid():
    job = Job(job_id="abc123", status=JobStatus.PROCESSING)
    assert job.video_url is None
    assert job.error is None
    assert job.stage is None
