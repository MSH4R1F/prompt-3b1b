"""Modal serverless app for ManimAI generation pipeline."""

import modal
from starlette.responses import JSONResponse

image = (
    modal.Image.from_registry("manimcommunity/manim:v0.20.1")
    .pip_install(
        "manim-voiceover[elevenlabs]",
        "elevenlabs==0.2.27",
        "anthropic",
        "boto3",
        "pydantic>=2.0",
    )
    .copy_local_dir("./manim_helpers", "/app/manim_helpers")
    .copy_local_dir("./prompts", "/app/prompts")
    .copy_local_dir("./pipeline", "/app/pipeline")
    .copy_local_dir("./schemas", "/app/schemas")
    .env({"PYTHONPATH": "/app"})
)

app = modal.App("manimator", image=image)
progress_store = modal.Dict.from_name("manimator-progress", create_if_missing=True)


@app.function(
    timeout=300,
    secrets=[
        modal.Secret.from_name("anthropic-key"),
        modal.Secret.from_name("elevenlabs-key"),
        modal.Secret.from_name("r2-credentials"),
    ],
)
def generate_video(prompt: str, duration: int = 60, audience: str = "beginner", voice: str = "Adam") -> dict:
    import os
    import pathlib
    import re
    import subprocess
    import sys
    import tempfile
    import uuid

    sys.path.insert(0, "/app")
    os.chdir("/app")

    from pipeline.coder import _call_claude, _load_prompt, _strip_code_fences, generate_scene_code
    from pipeline.planner import plan_lesson
    from pipeline.uploader import upload_to_r2

    job_id = str(uuid.uuid4())

    progress_store[job_id] = {"stage": "planning", "status": "processing"}
    plan = plan_lesson(prompt=prompt, duration=duration, audience=audience)

    progress_store[job_id] = {"stage": "coding", "status": "processing"}
    code = generate_scene_code(plan)

    match = re.search(r"class\s+(\w+)\s*\(", code)
    class_name = match.group(1) if match else "GeneratedScene"

    progress_store[job_id] = {"stage": "rendering", "status": "processing"}
    with tempfile.TemporaryDirectory() as tmpdir:
        scene_file = pathlib.Path(tmpdir) / "scene.py"
        scene_file.write_text(code)

        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")

        result = subprocess.run(
            ["manim", "render", "-qm", str(scene_file), class_name],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )

        if result.returncode != 0:
            repair_prompt = (
                _load_prompt("repair_system.txt")
                .replace("PLACEHOLDER_TRACEBACK", result.stderr[-3000:])
                .replace("PLACEHOLDER_ORIGINAL_CODE", code)
            )
            code = _strip_code_fences(_call_claude(repair_prompt, "Fix and return ONLY Python code."))
            match = re.search(r"class\s+(\w+)\s*\(", code)
            class_name = match.group(1) if match else class_name
            scene_file.write_text(code)
            result = subprocess.run(
                ["manim", "render", "-qm", str(scene_file), class_name],
                capture_output=True,
                text=True,
                cwd=tmpdir,
                env=env,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Render failed:\n{result.stderr[-2000:]}")

        mp4_files = list(pathlib.Path(tmpdir).rglob("*.mp4"))
        if not mp4_files:
            raise RuntimeError("Render succeeded but no .mp4 found")

        progress_store[job_id] = {"stage": "uploading", "status": "processing"}
        video_url = upload_to_r2(str(mp4_files[0]), job_id=job_id)

    return {"job_id": job_id, "video_url": video_url, "status": "completed"}


@app.function()
@modal.web_endpoint(method="POST")
def api_generate(request: dict):
    allowed_keys = {"prompt", "duration", "audience", "voice"}
    filtered = {key: value for key, value in request.items() if key in allowed_keys}

    if "prompt" not in filtered or not isinstance(filtered["prompt"], str):
        return JSONResponse({"error": "Missing or invalid 'prompt' field"}, status_code=400)

    if "duration" in filtered:
        filtered["duration"] = int(filtered["duration"])
        if filtered["duration"] not in (30, 60, 90):
            filtered["duration"] = 60

    if "audience" in filtered and filtered["audience"] not in (
        "beginner",
        "intermediate",
        "advanced",
    ):
        filtered["audience"] = "beginner"

    call = generate_video.spawn(**filtered)
    return JSONResponse({"job_id": call.object_id}, headers={"Access-Control-Allow-Origin": "*"})


@app.function()
@modal.web_endpoint(method="GET")
def api_status(job_id: str):
    from modal.functions import FunctionCall

    progress = progress_store.get(job_id, {})
    call = FunctionCall.from_id(job_id)
    try:
        result = call.get(timeout=0)
        return JSONResponse(
            {"status": "completed", **result}, headers={"Access-Control-Allow-Origin": "*"}
        )
    except TimeoutError:
        return JSONResponse(
            {"status": "processing", "stage": progress.get("stage", "planning")},
            headers={"Access-Control-Allow-Origin": "*"},
        )
    except Exception as exc:
        return JSONResponse(
            {"status": "failed", "error": str(exc)},
            headers={"Access-Control-Allow-Origin": "*"},
        )
