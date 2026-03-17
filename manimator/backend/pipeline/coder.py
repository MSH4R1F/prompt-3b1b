import inspect
import os
import pathlib
import re
import subprocess
import tempfile
import ast

import anthropic

import manim_helpers.tools as tools_module
from schemas.lesson import LessonPlan

_PROMPTS_DIR = pathlib.Path(__file__).parent.parent / "prompts"
_TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / "manim_helpers" / "templates"
_BACKEND_DIR = str(pathlib.Path(__file__).parent.parent)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def _load_prompt(name: str) -> str:
    return (_PROMPTS_DIR / name).read_text()


def _get_function_signatures() -> str:
    lines = []
    for name, func in inspect.getmembers(tools_module, inspect.isfunction):
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or ""
        lines.append(f"def {name}{sig}:\n    \"\"\"{doc}\"\"\"")
    return "\n\n".join(lines)


def _get_few_shot_examples() -> str:
    examples = []
    for file_path in sorted(_TEMPLATES_DIR.glob("*.py")):
        if file_path.name.startswith("__"):
            continue
        examples.append(f"# Example: {file_path.stem}\n{file_path.read_text()}")
    return "\n\n---\n\n".join(examples)


def _call_claude(system: str, user: str) -> str:
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def strip_code_fences(code: str) -> str:
    """Remove markdown code fences from LLM-generated Python code."""
    code = code.strip()
    if "```python" in code:
        code = code.split("```python", 1)[1]
        closing = code.find("```")
        if closing != -1:
            code = code[:closing]
    elif code.startswith("```"):
        first_newline = code.find("\n")
        if first_newline != -1:
            code = code[first_newline + 1:]
        closing = code.find("```")
        if closing != -1:
            code = code[:closing]
    return code.strip()


def _strip_non_python_prefix(code: str) -> str:
    """Remove any leading analysis text before the first Python statement."""
    lines = code.splitlines()
    starts = ("from ", "import ", "class ", "def ", "@")
    for i, line in enumerate(lines):
        if line.strip().startswith(starts):
            if i > 0:
                return "\n".join(lines[i:])
            break
    return code


def _sanitize_python_output(code: str) -> str:
    """Best-effort sanitizer for LLM Python output."""
    cleaned = _strip_non_python_prefix(strip_code_fences(code))
    try:
        ast.parse(cleaned)
        return cleaned
    except SyntaxError:
        return cleaned


def _try_render(code: str) -> tuple[bool, str]:
    """
    Write code to a temp file and attempt a real manim dry-run render.
    Falls back to py_compile if manim is unavailable.
    Returns (success, error_message).
    """
    # Write to system temp dir, not the source directory
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as file_obj:
        file_obj.write(code)
        file_path = file_obj.name

    try:
        match = re.search(r"class\s+(\w+)\s*\(", code)
        class_name = match.group(1) if match else "GeneratedScene"

        env = os.environ.copy()
        env["PYTHONPATH"] = _BACKEND_DIR + ":" + env.get("PYTHONPATH", "")

        result = subprocess.run(
            ["python", "-m", "manim", "render", "-ql", "--dry_run", file_path, class_name],
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        if result.returncode != 0:
            return False, result.stderr[-3000:]
        return True, ""
    except FileNotFoundError:
        result = subprocess.run(
            ["python", "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Render timed out after 60 seconds"
    except Exception as exc:
        return False, str(exc)
    finally:
        os.unlink(file_path)


def repair_code(code: str, error: str) -> str:
    """
    Ask Claude to fix a broken scene. Returns cleaned code (fences stripped).
    Public so modal_app.py can use it without importing private functions.
    """
    repair_prompt = (
        _load_prompt("repair_system.txt")
        .replace("PLACEHOLDER_TRACEBACK", error)
        .replace("PLACEHOLDER_ORIGINAL_CODE", code)
    )
    raw = _call_claude(repair_prompt, "Fix the error. Return ONLY corrected Python.")
    sanitized = _sanitize_python_output(raw)
    # If the repair response still isn't valid Python, keep the previous code.
    try:
        ast.parse(sanitized)
        return sanitized
    except SyntaxError:
        return code


def generate_scene_code(plan: LessonPlan, max_attempts: int = 3) -> str:
    coder_prompt = _load_prompt("coder_system.txt")
    coder_system = (
        coder_prompt.replace("PLACEHOLDER_FUNCTION_SIGNATURES", _get_function_signatures())
        .replace("PLACEHOLDER_FEW_SHOT_EXAMPLES", _get_few_shot_examples())
        .replace("PLACEHOLDER_LESSON_JSON", plan.model_dump_json(indent=2))
    )

    user_message = (
        "Generate a VoiceoverScene for the lesson plan above.\n"
        f"Topic: {plan.topic}. Audience: {plan.audience}. Duration target: {plan.duration}s.\n"
        "Return ONLY the Python code."
    )

    code = _sanitize_python_output(_call_claude(coder_system, user_message))

    for attempt in range(max_attempts):
        ok, error = _try_render(code)
        if ok:
            return code

        if attempt < max_attempts - 1:
            code = repair_code(code, error)

    # Always return fence-stripped code even if all attempts failed
    return _sanitize_python_output(code)
