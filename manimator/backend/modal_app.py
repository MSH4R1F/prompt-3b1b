"""Modal serverless app for ManimAI generation pipeline."""

import modal

image = (
    modal.Image.from_registry("manimcommunity/manim:v0.20.1")
    .apt_install("sox")
    .pip_install(
        "manim-voiceover[elevenlabs,whisper,gtts]",
        "elevenlabs==0.2.27",
        "gTTS",
        "requests",
        "anthropic",
        "boto3",
        "pydantic>=2.0",
        "fastapi",
        "setuptools<82",
    )
    .env({"PYTHONPATH": "/app"})
    .add_local_dir("./manim_helpers", "/app/manim_helpers")
    .add_local_dir("./prompts", "/app/prompts")
    .add_local_dir("./pipeline", "/app/pipeline")
    .add_local_dir("./schemas", "/app/schemas")
)

app = modal.App("manimator", image=image)
progress_store = modal.Dict.from_name("manimator-progress", create_if_missing=True)
BUILD_ID = "2026-03-09-ai-repair-loop-1"


@app.function(
    timeout=300,
    secrets=[
        modal.Secret.from_name("anthropic-key"),
        modal.Secret.from_name("elevenlabs-key"),
        modal.Secret.from_name("r2-credentials"),
    ],
)
def generate_video(
    request_id: str, prompt: str, duration: int = 60, audience: str = "beginner", voice: str = "Adam"
) -> dict:
    import ast
    import os
    import pathlib
    import re
    import requests
    import subprocess
    import sys
    import tempfile

    sys.path.insert(0, "/app")
    os.chdir("/app")

    from pipeline.coder import generate_scene_code, repair_code
    from pipeline.planner import plan_lesson
    from pipeline.uploader import upload_to_r2

    def _force_standard_voiceover(scene_code: str) -> str:
        """Normalize generated code to use our helper-backed ElevenLabs setup."""
        patched = scene_code

        has_local_setup = re.search(r"(?m)^def setup_voiceover\([^\)]*\):", patched) is not None
        uses_gtts = "GTTSService(" in patched
        uses_elevenlabs = "ElevenLabsService(" in patched

        # If code defines its own setup_voiceover, do not import the helper version
        # to avoid name shadowing confusion.
        if has_local_setup and "from manim_helpers.tools import setup_voiceover\n" in patched:
            patched = patched.replace("from manim_helpers.tools import setup_voiceover\n", "", 1)
            print(f"[generate_video] request_id={request_id} removed_helper_setup_import_due_local_def")

        # Ensure required imports are present for whatever setup function the code uses.
        if uses_gtts and "from manim_voiceover.services.gtts import GTTSService" not in patched:
            anchor = "from manim_voiceover import VoiceoverScene\n"
            add = "from manim_voiceover.services.gtts import GTTSService\n"
            if anchor in patched:
                patched = patched.replace(anchor, anchor + add, 1)
            else:
                patched = add + patched
            print(f"[generate_video] request_id={request_id} injected_gtts_import")

        if uses_elevenlabs and "from manim_voiceover.services.elevenlabs import ElevenLabsService" not in patched:
            anchor = "from manim_voiceover import VoiceoverScene\n"
            add = "from manim_voiceover.services.elevenlabs import ElevenLabsService\n"
            if anchor in patched:
                patched = patched.replace(anchor, anchor + add, 1)
            else:
                patched = add + patched
            print(f"[generate_video] request_id={request_id} injected_elevenlabs_import")

        if (
            "setup_voiceover(" in patched
            and "from manim_helpers.tools import setup_voiceover" not in patched
            and not has_local_setup
        ):
            # Insert import near the top-level import block.
            insert_after = "from manim_voiceover import VoiceoverScene\n"
            if insert_after in patched:
                patched = patched.replace(
                    insert_after,
                    insert_after + "from manim_helpers.tools import setup_voiceover\n",
                    1,
                )
            else:
                patched = "from manim_helpers.tools import setup_voiceover\n" + patched
            print(f"[generate_video] request_id={request_id} injected_setup_voiceover_import")
        # Prevent Whisper/transcription prompts in non-interactive containers.
        if "setup_voiceover(" in patched:
            patched, simple_calls = re.subn(
                r"setup_voiceover\(\s*self\s*\)",
                "setup_voiceover(self, use_bookmarks=False)",
                patched,
            )
            if simple_calls:
                print(
                    f"[generate_video] request_id={request_id} setup_voiceover_simple_calls="
                    f"{simple_calls} forced_use_bookmarks_false"
                )

            def _inject_use_bookmarks_false(match: re.Match) -> str:
                args = match.group(1)
                if "use_bookmarks" in args:
                    return match.group(0)
                args = args.strip()
                if not args:
                    return "setup_voiceover(self, use_bookmarks=False)"
                return f"setup_voiceover(self, {args}, use_bookmarks=False)"

            patched, param_calls = re.subn(
                r"setup_voiceover\(\s*self\s*,\s*([^\)]*)\)",
                _inject_use_bookmarks_false,
                patched,
            )
            if param_calls:
                print(
                    f"[generate_video] request_id={request_id} setup_voiceover_param_calls="
                    f"{param_calls} ensured_use_bookmarks_false"
                )
        # Ensure ElevenLabs does not auto-enable transcription unless explicitly required.
        if "ElevenLabsService(" in patched and "transcription_model" not in patched:
            patched = patched.replace(
                "ElevenLabsService(",
                "ElevenLabsService(transcription_model=None, ",
                1,
            )
            print(f"[generate_video] request_id={request_id} forced_transcription_model_none")
        return patched

    def _sanitize_for_latex_failure(scene_code: str) -> str:
        """
        Conservative fallback for LaTeX failures:
        - Prefer Text over Tex for plain labels.
        - Replace common Greek symbol labels with ASCII.
        """
        patched = scene_code
        replacements = {
            'x_label="θ"': 'x_label="theta"',
            "x_label='θ'": "x_label='theta'",
            'y_label="Δ"': 'y_label="delta"',
            "y_label='Δ'": "y_label='delta'",
        }
        for old, new in replacements.items():
            if old in patched:
                patched = patched.replace(old, new)
        if "Tex(" in patched:
            patched = patched.replace("Tex(", "Text(")
            print(f"[generate_video] request_id={request_id} replaced_tex_with_text")
        return patched

    def _strip_bookmark_timing(scene_code: str) -> str:
        """
        Remove bookmark-specific timing so Whisper transcription is not required.
        This prioritizes render reliability over bookmark-perfect sync.
        """
        patched = scene_code
        before = patched
        # Remove bookmark tags embedded in voiceover text.
        patched = re.sub(r"<bookmark mark=['\"][^'\"]+['\"]\s*/>", "", patched)
        # Remove explicit bookmark waits.
        patched = re.sub(r"^\s*self\.wait_until_bookmark\([^\)]*\)\s*$", "            self.wait(0.01)", patched, flags=re.MULTILINE)
        # Replace time_until_bookmark calls with remaining duration.
        patched = re.sub(
            r"tracker\.time_until_bookmark\([^\)]*\)",
            "max(0.2, tracker.get_remaining_duration())",
            patched,
        )
        # If transcription model was set to base for bookmarks, disable it after stripping.
        patched = patched.replace('transcription_model="base"', "transcription_model=None")
        if patched != before:
            print(f"[generate_video] request_id={request_id} stripped_bookmark_timing")
        return patched

    def _fallback_to_gtts(scene_code: str) -> str:
        """Replace ElevenLabs usage with GTTS for reliability fallback."""
        patched = scene_code

        if "from manim_voiceover.services.gtts import GTTSService" not in patched:
            if "from manim_voiceover import VoiceoverScene\n" in patched:
                patched = patched.replace(
                    "from manim_voiceover import VoiceoverScene\n",
                    "from manim_voiceover import VoiceoverScene\nfrom manim_voiceover.services.gtts import GTTSService\n",
                    1,
                )
            else:
                patched = "from manim_voiceover.services.gtts import GTTSService\n" + patched

        # Remove helper import and provide a local setup_voiceover for deterministic GTTS fallback.
        patched = patched.replace("from manim_helpers.tools import setup_voiceover\n", "")
        if re.search(r"(?m)^def setup_voiceover\([^\)]*\):", patched):
            patched = re.sub(
                r"(?ms)^def setup_voiceover\([^\)]*\):\n(?:[ \t]+.*\n)+",
                "def setup_voiceover(scene):\n    scene.set_speech_service(GTTSService())\n\n",
                patched,
                count=1,
            )
        elif "setup_voiceover(self)" in patched:
            anchor = "from manim_voiceover.services.gtts import GTTSService\n"
            inject = (
                "def setup_voiceover(scene):\n"
                "    scene.set_speech_service(GTTSService())\n\n"
            )
            if anchor in patched:
                patched = patched.replace(anchor, anchor + inject, 1)
            else:
                patched = inject + patched

        # Replace direct ElevenLabs speech service initialization.
        patched = re.sub(
            r"self\.set_speech_service\(ElevenLabsService\([^\)]*\)\)",
            "self.set_speech_service(GTTSService())",
            patched,
        )

        # Keep render deterministic: remove bookmark-driven timing.
        patched = _strip_bookmark_timing(patched)
        print(f"[generate_video] request_id={request_id} applied_gtts_fallback")
        return patched

    def _strip_non_python_prefix(scene_code: str) -> str:
        """
        Claude sometimes prepends analysis text before code.
        Keep content from the first likely Python line.
        """
        lines = scene_code.splitlines()
        first_py_idx = None
        py_starts = ("from ", "import ", "class ", "def ", "@")
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(py_starts):
                first_py_idx = idx
                break
        if first_py_idx is not None and first_py_idx > 0:
            print(
                f"[generate_video] request_id={request_id} stripped_non_python_prefix_lines="
                f"{first_py_idx}"
            )
            return "\n".join(lines[first_py_idx:])
        return scene_code

    def _safe_fallback_scene() -> str:
        """Always-valid emergency scene so pipeline never writes broken fragments."""
        safe_topic = (prompt or "math concept").replace('"', "").strip()[:60]
        return f'''from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.gtts import GTTSService


class GeneratedFallbackScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(GTTSService())
        title = Text("{safe_topic}", font_size=42)
        subtitle = Text("Auto-fallback scene", font_size=24).next_to(title, DOWN, buff=0.35)
        with self.voiceover(text="Here is a fallback explainer scene generated after an internal code error."):
            self.play(FadeIn(title, shift=DOWN), run_time=0.8)
            self.play(FadeIn(subtitle, shift=UP), run_time=0.8)
        self.wait(0.5)
'''

    def _ensure_valid_python(scene_code: str) -> str:
        """Best-effort syntax sanitization before writing scene.py."""
        cleaned = _strip_non_python_prefix(scene_code)
        try:
            ast.parse(cleaned)
            has_scene_class = "VoiceoverScene" in cleaned and "class " in cleaned
            has_construct = "def construct(" in cleaned
            if has_scene_class and has_construct:
                return cleaned
            print(
                f"[generate_video] request_id={request_id} structure_check_failed "
                f"has_scene_class={has_scene_class} has_construct={has_construct}"
            )
            return _safe_fallback_scene()
        except SyntaxError as exc:
            print(f"[generate_video] request_id={request_id} syntax_precheck_failed={exc}")
            return _safe_fallback_scene()

    def _preflight_elevenlabs() -> bool:
        """Log detailed ElevenLabs diagnostics before render."""
        key = os.environ.get("ELEVEN_API_KEY", "")
        masked = f"...{key[-4:]}" if key else "<missing>"
        print(
            f"[generate_video] request_id={request_id} elevenlabs_env "
            f"key_present={bool(key)} key_len={len(key)} key_tail={masked}"
        )
        if not key:
            return False
        try:
            resp = requests.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": key},
                timeout=15,
            )
            body_preview = (resp.text or "")[:280].replace("\n", " ")
            print(
                f"[generate_video] request_id={request_id} elevenlabs_probe "
                f"status={resp.status_code} body_preview={body_preview}"
            )
            return resp.status_code == 200
        except Exception as exc:
            print(f"[generate_video] request_id={request_id} elevenlabs_probe_error={exc}")
            return False

    def _ensure_bookmark_transcription(scene_code: str) -> str:
        """
        If generated code uses bookmarks, ensure ElevenLabsService has
        transcription_model enabled so bookmark timing works.
        """
        uses_bookmarks = (
            "wait_until_bookmark(" in scene_code
            or "time_until_bookmark(" in scene_code
            or "<bookmark mark=" in scene_code
        )
        has_transcription = "transcription_model" in scene_code
        has_elevenlabs_ctor = "ElevenLabsService(" in scene_code
        has_setup_voiceover = "setup_voiceover(" in scene_code
        has_use_bookmarks_false = "use_bookmarks=False" in scene_code
        print(
            f"[generate_video] request_id={request_id} bookmark_scan "
            f"uses_bookmarks={uses_bookmarks} has_transcription={has_transcription} "
            f"has_elevenlabs_ctor={has_elevenlabs_ctor} has_setup_voiceover={has_setup_voiceover} "
            f"has_use_bookmarks_false={has_use_bookmarks_false}"
        )

        if not uses_bookmarks:
            return scene_code
        if has_transcription:
            return scene_code

        patched_code = scene_code
        patched = False

        # Most common failure: generated helper call explicitly disables bookmarks.
        if "use_bookmarks=False" in patched_code:
            patched_code = patched_code.replace("use_bookmarks=False", "use_bookmarks=True")
            patched = True
            print(f"[generate_video] request_id={request_id} patched_use_bookmarks_true")

        # Ensure direct ElevenLabsService constructor includes transcription model.
        if "ElevenLabsService(" in patched_code and "transcription_model" not in patched_code:
            patched_code = patched_code.replace(
                "ElevenLabsService(",
                'ElevenLabsService(transcription_model="base", ',
                1,
            )
            patched = True
            print(f"[generate_video] request_id={request_id} patched_transcription_model_base")

        if not patched:
            print(
                f"[generate_video] request_id={request_id} bookmark_patch_noop "
                "could_not_infer_patch_target"
            )

        # Debug helper lines to confirm how speech service is wired in generated code.
        speech_lines = [
            line.strip()
            for line in patched_code.splitlines()
            if ("setup_voiceover(" in line or "ElevenLabsService(" in line or "set_speech_service(" in line)
        ]
        if speech_lines:
            preview = " | ".join(speech_lines[:4])
            print(f"[generate_video] request_id={request_id} speech_lines={preview}")
        else:
            print(f"[generate_video] request_id={request_id} speech_lines=none_found")

        if patched:
            return patched_code

        if "ElevenLabsService(" in scene_code:
            patched = scene_code.replace(
                "ElevenLabsService(",
                'ElevenLabsService(transcription_model="base", ',
                1,
            )
            print(f"[generate_video] request_id={request_id} patched_transcription_model=base")
            return patched
        return scene_code

    print(
        f"[generate_video] request_id={request_id} start "
        f"build={BUILD_ID} prompt_len={len(prompt)} duration={duration} audience={audience} voice={voice}"
    )
    progress = progress_store.get(request_id, {})
    progress.update({"stage": "planning", "status": "processing"})
    progress_store[request_id] = progress
    print(f"[generate_video] request_id={request_id} stage=planning")
    plan = plan_lesson(prompt=prompt, duration=duration, audience=audience)
    print(f"[generate_video] request_id={request_id} planning_done segments={len(plan.segments)}")

    progress.update({"stage": "coding", "status": "processing"})
    progress_store[request_id] = progress
    print(f"[generate_video] request_id={request_id} stage=coding")
    code = generate_scene_code(plan)
    code = _force_standard_voiceover(code)
    code = _ensure_bookmark_transcription(code)
    code = _strip_bookmark_timing(code)
    code = _ensure_valid_python(code)
    print(f"[generate_video] request_id={request_id} coding_done code_len={len(code)}")

    match = re.search(r"class\s+(\w+)\s*\(", code)
    class_name = match.group(1) if match else "GeneratedScene"
    print(f"[generate_video] request_id={request_id} class_name={class_name}")

    progress.update({"stage": "rendering", "status": "processing"})
    progress_store[request_id] = progress
    print(f"[generate_video] request_id={request_id} stage=rendering")
    with tempfile.TemporaryDirectory() as tmpdir:
        scene_file = pathlib.Path(tmpdir) / "scene.py"
        scene_file.write_text(code)

        env = os.environ.copy()
        env["PYTHONPATH"] = "/app:" + env.get("PYTHONPATH", "")
        elevenlabs_ok = _preflight_elevenlabs()
        if not elevenlabs_ok:
            print(
                f"[generate_video] request_id={request_id} elevenlabs_unavailable "
                "forcing_gtts_before_render"
            )
            code = _fallback_to_gtts(code)
            code = _ensure_valid_python(code)
            scene_file.write_text(code)

        render_attempt = 1
        result = subprocess.run(
            ["manim", "render", "-qm", str(scene_file), class_name],
            capture_output=True,
            text=True,
            cwd=tmpdir,
            env=env,
        )
        print(
            f"[generate_video] request_id={request_id} render_attempt={render_attempt} returncode={result.returncode}"
        )

        if result.returncode != 0:
            print(
                f"[generate_video] request_id={request_id} render_error_1="
                f"{result.stderr[-1200:]}"
            )
            if "Failed to initialize ElevenLabs" in result.stderr:
                print(
                    f"[generate_video] request_id={request_id} detected_elevenlabs_init_failure "
                    "retrying_with_gtts"
                )
                code = _fallback_to_gtts(code)
                scene_file.write_text(code)
                render_attempt += 1
                result = subprocess.run(
                    ["manim", "render", "-qm", str(scene_file), class_name],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir,
                    env=env,
                )
                print(
                    f"[generate_video] request_id={request_id} render_attempt={render_attempt} "
                    f"mode=gtts_fallback returncode={result.returncode}"
                )
                if result.returncode != 0:
                    print(
                        f"[generate_video] request_id={request_id} render_error_{render_attempt}="
                        f"{result.stderr[-1200:]}"
                    )
            # One deterministic retry for common LaTeX issues.
            if result.returncode != 0 and "latex error converting to dvi" in result.stderr.lower():
                print(f"[generate_video] request_id={request_id} latex_fallback_retry=1")
                code = _sanitize_for_latex_failure(code)
                scene_file.write_text(code)
                render_attempt += 1
                result = subprocess.run(
                    ["manim", "render", "-qm", str(scene_file), class_name],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir,
                    env=env,
                )
                print(
                    f"[generate_video] request_id={request_id} render_attempt={render_attempt} "
                    f"mode=latex_fallback returncode={result.returncode}"
                )
                if result.returncode == 0:
                    print(f"[generate_video] request_id={request_id} latex_fallback_success")
                else:
                    print(
                        f"[generate_video] request_id={request_id} render_error_{render_attempt}="
                        f"{result.stderr[-1200:]}"
                    )

            # Generic self-heal retry loop using Anthropic repair prompt.
            max_ai_repairs = 2
            ai_repair_count = 0
            while result.returncode != 0 and ai_repair_count < max_ai_repairs:
                ai_repair_count += 1
                repair_context = (result.stderr or "")[-4000:]
                print(
                    f"[generate_video] request_id={request_id} ai_repair_attempt={ai_repair_count} "
                    f"error_tail={repair_context[-300:].replace(chr(10), ' ')}"
                )
                try:
                    repaired = repair_code(code, repair_context)
                except Exception as exc:
                    print(
                        f"[generate_video] request_id={request_id} ai_repair_attempt={ai_repair_count} "
                        f"repair_call_failed={exc}"
                    )
                    break

                repaired = _force_standard_voiceover(repaired)
                repaired = _ensure_bookmark_transcription(repaired)
                repaired = _strip_bookmark_timing(repaired)
                repaired = _ensure_valid_python(repaired)

                if repaired == code:
                    print(
                        f"[generate_video] request_id={request_id} ai_repair_attempt={ai_repair_count} "
                        "code_unchanged=True"
                    )

                code = repaired
                scene_file.write_text(code)

                match = re.search(r"class\s+(\w+)\s*\(", code)
                class_name = match.group(1) if match else class_name
                print(
                    f"[generate_video] request_id={request_id} ai_repair_attempt={ai_repair_count} "
                    f"class_name={class_name} code_len={len(code)}"
                )

                render_attempt += 1
                result = subprocess.run(
                    ["manim", "render", "-qm", str(scene_file), class_name],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir,
                    env=env,
                )
                print(
                    f"[generate_video] request_id={request_id} render_attempt={render_attempt} "
                    f"mode=ai_repair_{ai_repair_count} returncode={result.returncode}"
                )
                if result.returncode != 0:
                    print(
                        f"[generate_video] request_id={request_id} render_error_{render_attempt}="
                        f"{result.stderr[-1200:]}"
                    )

            if result.returncode != 0:
                head_preview = "\n".join(code.splitlines()[:80])
                print(f"[generate_video] request_id={request_id} scene_head_preview=\n{head_preview}")
                raise RuntimeError(f"Render failed:\n{result.stderr[-2000:]}")

        mp4_files = list(pathlib.Path(tmpdir).rglob("*.mp4"))
        if not mp4_files:
            raise RuntimeError("Render succeeded but no .mp4 found")

        # Prefer the final rendered scene file (usually <ClassName>.mp4), not
        # intermediate segment files that may be silent.
        final_named = [p for p in mp4_files if p.name == f"{class_name}.mp4"]
        if final_named:
            selected_mp4 = max(final_named, key=lambda p: p.stat().st_size)
        else:
            selected_mp4 = max(mp4_files, key=lambda p: p.stat().st_size)
        print(
            f"[generate_video] request_id={request_id} mp4_selected={selected_mp4} "
            f"size={selected_mp4.stat().st_size}"
        )

        progress.update({"stage": "uploading", "status": "processing"})
        progress_store[request_id] = progress
        print(f"[generate_video] request_id={request_id} stage=uploading")
        video_url = upload_to_r2(str(selected_mp4), job_id=request_id)
        print(f"[generate_video] request_id={request_id} upload_done url={video_url}")

    progress.update({"stage": "completed", "status": "completed", "video_url": video_url})
    progress_store[request_id] = progress
    print(f"[generate_video] request_id={request_id} completed")
    return {"job_id": request_id, "video_url": video_url, "status": "completed"}


@app.function()
@modal.fastapi_endpoint(method="POST")
def api_generate(request: dict):
    import uuid

    allowed_keys = {"prompt", "duration", "audience", "voice"}
    filtered = {key: value for key, value in request.items() if key in allowed_keys}

    if "prompt" not in filtered or not isinstance(filtered["prompt"], str):
        return {"error": "Missing or invalid 'prompt' field"}, 400

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

    request_id = str(uuid.uuid4())
    call = generate_video.spawn(request_id=request_id, **filtered)
    print(
        f"[api_generate] request_id={request_id} call_id={call.object_id} "
        f"build={BUILD_ID} duration={filtered.get('duration', 60)} audience={filtered.get('audience', 'beginner')}"
    )
    progress_store[request_id] = {
        "status": "processing",
        "stage": "planning",
        "call_id": call.object_id,
    }
    return {"job_id": request_id}


@app.function()
@modal.fastapi_endpoint(method="GET")
def api_status(job_id: str):
    from modal.functions import FunctionCall

    progress = progress_store.get(job_id, {})
    call_id = progress.get("call_id")
    if not call_id:
        print(f"[api_status] job_id={job_id} unknown_job")
        return {"status": "failed", "error": "Unknown job_id"}

    call = FunctionCall.from_id(call_id)
    try:
        result = call.get(timeout=0)
        print(f"[api_status] job_id={job_id} call_id={call_id} status=completed")
        progress.update({"status": "completed", "stage": "completed"})
        progress_store[job_id] = progress
        return {"status": "completed", **result}
    except TimeoutError:
        print(
            f"[api_status] job_id={job_id} call_id={call_id} status=processing "
            f"stage={progress.get('stage', 'planning')}"
        )
        return {"status": "processing", "stage": progress.get("stage", "planning")}
    except Exception as exc:
        print(f"[api_status] job_id={job_id} call_id={call_id} status=failed error={exc}")
        progress.update({"status": "failed", "error": str(exc)})
        progress_store[job_id] = progress
        return {"status": "failed", "error": str(exc)}
