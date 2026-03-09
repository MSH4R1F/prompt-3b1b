import pathlib
import re

from pipeline.coder import generate_scene_code
from pipeline.planner import plan_lesson


def _sanitize_class_name(topic: str) -> str:
    words = topic.split()[:3]
    name = "".join(re.sub(r"[^a-zA-Z0-9]", "", word).capitalize() for word in words)
    if not name or not name[0].isalpha():
        name = "Generated" + name
    return name + "Scene"


def run_pipeline_local(
    prompt: str,
    duration: int = 60,
    audience: str = "beginner",
    output_dir: str = ".",
    skip_pedagogy: bool = True,
) -> str:
    print(f"[Stage 1] Planning lesson for: {prompt}")
    plan = plan_lesson(prompt=prompt, duration=duration, audience=audience)
    print(f"  -> {len(plan.segments)} segments planned")

    if not skip_pedagogy:
        from pipeline.pedagogy import pedagogy_check

        print("[Stage 2] Pedagogy review...")
        plan = pedagogy_check(plan)
        print(f"  -> Plan reviewed, {len(plan.segments)} segments")

    print("[Stage 3] Generating scene code...")
    code = generate_scene_code(plan)
    print(f"  -> {len(code)} characters generated")

    match = re.search(r"class\s+(\w+)\s*\(", code)
    class_name = match.group(1) if match else _sanitize_class_name(plan.topic)

    output_path = pathlib.Path(output_dir) / f"{class_name}.py"
    output_path.write_text(code)
    print(f"  -> Written to {output_path}")
    print(f"  -> Render with: PYTHONPATH=. manim render -qm {output_path} {class_name}")
    return str(output_path)


if __name__ == "__main__":
    import sys

    prompt_text = " ".join(sys.argv[1:]) or "explain binary search"
    scene_path = run_pipeline_local(prompt=prompt_text, duration=60)
    print(f"\nScene written to: {scene_path}")
