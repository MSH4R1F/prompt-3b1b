"""Integration tests for pipeline stages. Slow tests require external APIs."""

import pathlib
from unittest.mock import MagicMock, patch

import pytest

from schemas.lesson import LessonPlan, Segment


def _minimal_plan() -> LessonPlan:
    return LessonPlan(
        topic="addition",
        audience="beginner",
        duration=20,
        segments=[
            Segment(
                narration="Two plus two equals four.",
                visual_intent=["formula"],
                text_classes={"formula": "MathTex"},
                positions={"formula": "center"},
                suggested_helpers=["safe_mathtex"],
            )
        ],
    )


@pytest.mark.slow
def test_plan_lesson_returns_valid_schema():
    from pipeline.planner import plan_lesson

    plan = plan_lesson(prompt="Explain binary search to a beginner", duration=45, audience="beginner")
    assert isinstance(plan, LessonPlan)
    assert plan.topic != ""
    assert 1 <= len(plan.segments) <= 5
    for seg in plan.segments:
        assert seg.narration != ""
        assert len(seg.visual_intent) > 0


@pytest.mark.slow
def test_generate_scene_code_produces_python():
    from pipeline.coder import generate_scene_code

    code = generate_scene_code(_minimal_plan())
    assert "class" in code
    assert "VoiceoverScene" in code
    assert "def construct" in code
    assert "from manim import" in code


@pytest.mark.slow
def test_end_to_end_local(tmp_path):
    from pipeline.orchestrator import run_pipeline_local

    output_path = run_pipeline_local(
        prompt="Explain what addition is to a 5-year-old",
        duration=20,
        audience="beginner",
        output_dir=str(tmp_path),
    )
    assert pathlib.Path(output_path).exists()
    assert output_path.endswith(".py")
    content = pathlib.Path(output_path).read_text()
    assert "VoiceoverScene" in content


def test_upload_to_r2_calls_boto3(tmp_path, monkeypatch):
    monkeypatch.setenv("R2_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("R2_ACCESS_KEY", "test-key")
    monkeypatch.setenv("R2_SECRET_KEY", "test-secret")
    monkeypatch.setenv("R2_BUCKET", "test-bucket")
    monkeypatch.setenv("R2_PUBLIC_URL", "https://pub-test.r2.dev")

    video_file = tmp_path / "test.mp4"
    video_file.write_bytes(b"fake mp4 content")

    with patch("pipeline.uploader.boto3.client") as mock_boto3:
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client

        from pipeline.uploader import upload_to_r2

        url = upload_to_r2(str(video_file), job_id="test123")

        mock_client.put_object.assert_called_once()
        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == "videos/test123.mp4"
        assert call_kwargs["ContentType"] == "video/mp4"
        assert url == "https://pub-test.r2.dev/videos/test123.mp4"


@pytest.mark.slow
def test_pedagogy_check_returns_valid_plan():
    from pipeline.pedagogy import pedagogy_check

    reviewed = pedagogy_check(_minimal_plan())
    assert isinstance(reviewed, LessonPlan)
    assert reviewed.topic == "addition"
    assert len(reviewed.segments) >= 1
