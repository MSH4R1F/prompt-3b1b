# ManimAI — Master Build Plan (v4)

> **Versions locked to:** Manim Community v0.20.1 (Feb 2026) · manim-voiceover v0.3.7 · Python 3.10+
> This document is the single source of truth. All prompts, helpers, failure rules, and architecture live here.

---

## One-line summary

A Next.js web app where you type a prompt and get back a narrated Manim explainer video — powered by Claude, ElevenLabs, VoiceoverScene, and Modal.

---

## What Changed Since v3

| What | v3 | v4 (this plan) | Why |
|------|----|----------------|-----|
| Manim target version | v0.18.1 | v0.20.1 | Current release; 7 breaking changes that break LLM code |
| tools.py | 8 functions | 12 functions with v0.20 correct APIs | Overflow protection, Code block helper, `highlight_box`, `setup_voiceover` |
| Coder system prompt | Basic rules | Full failure-mode ruleset (Categories A–F, 22 rules) | TheoremExplainAgent study: API hallucination is #1 failure source |
| ElevenLabs SDK | Unspecified | Pin `elevenlabs==0.2.27` | Current SDK (v1.50+/v2.1+) is incompatible with manim-voiceover v0.3.7 |
| VoiceoverScene docs | Overview | Exhaustive: all tracker props, caching behavior, bookmark spec | Avoid FM-C class errors |
| System prompts | 3 prompts | 4 prompts + few-shot examples embedded | Coder needs examples, not just rules |
| Modal image | `manimcommunity/manim:v0.18.1` | `manimcommunity/manim:v0.20.1` | Match target version |

---

## The 5-Stage Pipeline (unchanged architecture, updated internals)

```
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 1: PLANNER + SCRIPTWRITER                      Claude API  │
│                                                                  │
│ Input:  "Explain gradient descent to a beginner in 60 seconds"  │
│ Output: Structured lesson JSON with per-segment narration        │
│                                                                  │
│ Single LLM call. Produces both lesson structure AND narration.   │
│                                                                  │
│ {                                                                │
│   "topic": "gradient descent",                                   │
│   "audience": "beginner",                                        │
│   "segments": [                                                  │
│     {                                                            │
│       "narration": "Imagine you're lost in the mountains...",   │
│       "visual_intent": ["axes", "curve", "dot_on_curve"],       │
│       "text_classes": {"title": "Text", "formula": "MathTex"},  │
│       "positions": {"title": "top", "axes": "center"},          │
│       "suggested_helpers": ["create_axes", "plot_function"]     │
│     }                                                            │
│   ]                                                              │
│ }                                                                │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 2: PEDAGOGY CHECK (optional)                   Claude API  │
│                                                                  │
│ Input:  Lesson JSON from Stage 1                                 │
│ Output: Revised lesson JSON (or approved as-is)                  │
│                                                                  │
│ - Is any segment too fast for the audience level?                │
│ - Are visuals shown BEFORE verbal explanation? (bad)             │
│ - Is flow: setup → concept → example → summary?                 │
│ - Are text_classes correct (Text vs MathTex vs Tex)?            │
│ - Are positions specified to avoid ORIGIN stacking?             │
│                                                                  │
│ ~500 tokens. Skip in "fast mode" if needed.                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 3: AGENTIC CODER                               Claude API  │
│                                                                  │
│ Input:  Lesson JSON + tools.py signatures + few-shot examples   │
│ Output: Complete VoiceoverScene Python class                     │
│                                                                  │
│ REPAIR LOOP (max 3 attempts):                                    │
│   while attempt < 3:                                             │
│       code = generate_manim(lesson_json)                         │
│       result = render(code)                                      │
│       if result.success: break                                   │
│       context += f"\nError: {result.traceback}"                  │
│       attempt += 1                                               │
│                                                                  │
│ CACHING NOTE: Changing animation code does NOT re-call           │
│ ElevenLabs (audio cached by text content). Repair loops are      │
│ cheap. Only changing narration text costs TTS credits.           │
│                                                                  │
│ Model: Claude Sonnet (cost-efficient for retries)               │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 4: RENDER                          Modal (serverless CPU)  │
│                                                                  │
│ Input:  Generated .py scene file + tools.py                      │
│ Output: .mp4 (video with audio merged by VoiceoverScene)         │
│                                                                  │
│ Container: manimcommunity/manim:v0.20.1                          │
│   + manim-voiceover[elevenlabs] (pins elevenlabs==0.2.27)       │
│   + anthropic, boto3, pydantic>=2.0                              │
│                                                                  │
│ Command: manim render -qm scene.py ClassName                     │
│   -ql = 480p (fast, for testing)                                 │
│   -qm = 720p (web default)                                       │
│   -qh = 1080p (final quality)                                    │
│                                                                  │
│ If render fails → traceback sent back to Stage 3                 │
│ If render succeeds → .mp4 with audio already included            │
│                                                                  │
│ NO FFmpeg merge step needed. VoiceoverScene handles it.          │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ STAGE 5: UPLOAD + DELIVER                                        │
│                                                                  │
│ 1. Upload .mp4 to Cloudflare R2                                  │
│ 2. (Optional) Generate .srt from narration text                  │
│ 3. Update job status → "completed" with video_url               │
│ 4. Frontend receives URL, shows video player                     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Critical: Manim v0.18 → v0.20 Breaking Changes

**Any LLM trained on pre-2025 tutorials will generate code that breaks on these.** The system prompt and tools.py must guard against all seven.

### 1. Code mobject — complete constructor rewrite (v0.19)

| Old (v0.18) | New (v0.19+) |
|---|---|
| `file_name` | `code_file` |
| `code` | `code_string` |
| `style` | `formatter_style` |
| `insert_line_no` | `add_line_numbers` |
| `line_no_from` | `line_numbers_from` |
| `font`, `font_size` | `paragraph_config={"font": ..., "font_size": ...}` |
| `margin`, `corner_radius` | `background_config={"buff": ..., "corner_radius": ...}` |

Use the `code_block()` helper to avoid this entirely.

### 2. SurroundingRectangle — positional args removed (v0.19)

`SurroundingRectangle(mob, RED, 0.3)` fails. Must use:
`SurroundingRectangle(mob, color=RED, buff=0.3)`

Use `highlight_box()` helper.

### 3. MathTex submobject indices changed (v0.20)

`{{ }}` isolation logic was rewritten. Code using `eq[2]` to target parts may break.

### 4. Deprecated class names (removed long ago, still hallucinated)

`TextMobject` → `Tex` · `TexMobject` → `MathTex` · `ShowCreation` → `Create` · `CONFIG = {}` → constructor kwargs

### 5. Sector constructor changed

`Sector(inner_radius=, outer_radius=)` → use `AnnularSector` or `Sector(radius=, angle=)`

### 6. ImageMobject resampling

`lanczos`, `box`, `hamming` removed. Only `nearest`, `linear`, `cubic` remain.

### 7. ffmpeg no longer required

Manim v0.20 uses `pyav` internally. Do not install or call ffmpeg directly.

### New v0.20 idioms to USE (teach LLM these)

- `ax @ (x, y)` — shorthand for `ax.coords_to_point(x, y)` — use this
- `mob.always.next_to(other, UP)` — persistent updater without `add_updater`
- `VGroup(squares)` — accepts iterables, no need to unpack `*`
- `ManimColor.darker(0.3)` / `.lighter(0.2)` / `.contrasting()` — dynamic colors
- `PURE_CYAN`, `PURE_MAGENTA`, `PURE_YELLOW` — new in v0.20
- `Scene.time` property — current render time

---

## ElevenLabs SDK — Critical Deployment Issue

`manim-voiceover` v0.3.7 pins `elevenlabs ^0.2.27`. The current ElevenLabs SDK (v1.50+/v2.1+) is **incompatible**.

**Solution: pin the version explicitly.**

```
# requirements.txt
manim-voiceover[elevenlabs]
elevenlabs==0.2.27
```

Or use `manim-voiceover-enhanced` which supports the new SDK. Build this check into Modal image definition.

---

## VoiceoverScene Deep Dive

### All tracker properties

| Property / Method | Type | Description |
|---|---|---|
| `tracker.duration` | `float` | Total audio duration in seconds |
| `tracker.start_t` | `float` | Scene render time when voiceover starts |
| `tracker.end_t` | `float` | `start_t + duration` |
| `tracker.data` | `dict` | Full TTS result including `word_boundaries` |
| `tracker.bookmark_times` | `dict` | `{name: absolute_scene_time}` — requires transcription model |
| `tracker.get_remaining_duration(buff=0)` | method → `float` | `max(end_t - current_time + buff, 0)` |
| `tracker.time_until_bookmark(mark, buff=0, limit=None)` | method → `float` | Seconds until named bookmark |

### Bookmark specification

Format: `<bookmark mark='name'/>` (self-closing XML tag).

**Name rules:** word characters only (letters, digits, underscores). **No hyphens or spaces.**

Both quote styles work: `mark='A'` and `mark="A"`.

**Bookmarks require** `transcription_model="base"` in the service constructor. Without it, they use inaccurate linear interpolation or raise exceptions.

### Three canonical timing patterns

**Pattern 1 — Single animation, full duration:**
```python
with self.voiceover(text="This circle appears now.") as tracker:
    self.play(Create(circle), run_time=tracker.duration)
```

**Pattern 2 — Multiple animations with bookmarks:**
```python
with self.voiceover(
    text="First we <bookmark mark='draw'/>draw a circle, "
         "then <bookmark mark='color'/>color it red."
) as tracker:
    self.wait_until_bookmark("draw")
    self.play(Create(circle),
              run_time=tracker.time_until_bookmark("color"))
    self.wait_until_bookmark("color")
    self.play(circle.animate.set_color(RED),
              run_time=tracker.get_remaining_duration())
```

**Pattern 3 — Subdividing without bookmarks:**
```python
with self.voiceover(text="Two steps in sequence.") as tracker:
    self.play(Create(circle), run_time=tracker.duration * 0.5)
    self.play(circle.animate.shift(RIGHT),
              run_time=tracker.get_remaining_duration())
```

### Caching behavior (critical for repair loops)

- Cache location: `{config.media_dir}/voiceovers/`
- Cache key: input text **with bookmarks stripped** + service config (voice, model)
- **Changing only animation code → no TTS re-call** (excellent for repair loops)
- **Changing bookmark positions only → no TTS re-call** (times recomputed from cached word boundaries)
- **Changing narration text → new TTS call**
- To force regeneration: delete the cache directory

### VoiceoverScene pitfalls

- `set_speech_service()` must be called before any voiceover
- SSML is not implemented — `self.voiceover(ssml=...)` raises `NotImplementedError`
- The `with` block auto-calls `wait_for_voiceover()` on exit — never call it manually inside
- `safe_wait()` silently does nothing for sub-frame durations
- TTS is synchronous — audio is generated when entering the `with` block

---

## Failure Mode Catalog

Include the relevant rules from each category in the coder system prompt.

### Category A: LaTeX errors

**FM-A1: Missing raw string.** `MathTex("\\frac{1}{2}")` → escape bugs. **RULE: ALL LaTeX strings use `r"..."` raw string syntax.**

**FM-A2: Text content in MathTex.** `MathTex(r"The equation is E=mc^2")` fails (math mode wrapper). **RULE: `MathTex` = pure math only. For mixed: `Tex(r"The equation is $E=mc^2$")`.**

**FM-A3: LaTeX in Text().** `Text(r"\frac{1}{2}")` renders literal backslash. **RULE: `Text()` for plain text only.**

**FM-A4: Unbalanced braces across MathTex args.** Each arg is compiled separately. **RULE: Every string arg to MathTex/Tex must be brace-balanced.**

**FM-A5: `{{ }}` misuse.** Only for submobject splitting (TransformMatchingTex). Not standard LaTeX grouping.

**FM-A6: Unavailable packages.** Default includes only `amsmath`, `amssymb`, `babel`. `\mathscr`, `\coloneqq` etc. fail. **RULE: Only amsmath/amssymb unless explicit TexTemplate.**

### Category B: Animation logic errors

**FM-B1: `.animate` rotation ≥ 90°.** Interpolates start→end, 180° rotation = same state = invisible. **RULE: Use `Rotate(mob, angle)` for ≥ 90°.**

**FM-B2: Transform reference confusion.** After `Transform(A, B)` → reference `A`. After `ReplacementTransform(A, B)` → reference `B`.

**FM-B3: Animating unadded objects.** Object must be in scene before `.animate`. Add via `self.add()` or creation animation first.

**FM-B4: Conflicting `.animate` on same object.** Two separate `.animate` builders conflict. **RULE: Chain: `mob.animate.shift(RIGHT).scale(2)`.**

### Category C: VoiceoverScene timing errors

**FM-C1: `tracker.duration` for multiple animations.** Each gets full duration → total = 2–3×. **RULE: Never use `tracker.duration` for more than one animation. Use `get_remaining_duration()` or bookmarks.**

**FM-C2: Bookmarks without transcription model.** Requires `transcription_model="base"`. **RULE: Always set this when using bookmarks.**

**FM-C3: Animations outside the `with` block.** Won't sync to voiceover. **RULE: ALL synced animations inside the `with self.voiceover()` block.**

**FM-C4: Wrong base class.** `class MyScene(Scene):` → `AttributeError: no attribute 'voiceover'`. **RULE: Must inherit from `VoiceoverScene`.**

### Category D: Coordinate and positioning errors

**FM-D1: Objects off-screen.** Frame is ~14.22 × 8.0 units. **RULE: Keep content within X ∈ [-6.5, 6.5], Y ∈ [-3.5, 3.5].**

**FM-D2: Objects stacked at ORIGIN.** All mobjects default to center. **RULE: Always position explicitly with `arrange()`, `next_to()`, `to_edge()`, or `move_to()`.**

**FM-D3: Pixel values as coordinates.** `move_to([960, 540, 0])` puts object astronomically off-screen. **RULE: Scene units only. Width ≈ 14.22, height = 8.0.**

**FM-D4: Text overflow.** Long text/equations exceed frame. **RULE: Use `mob.scale_to_fit_width(config.frame_width - 2)` for potentially long content.** Use `safe_text()` / `safe_mathtex()` helpers.

### Category E: Import and version errors

**FM-E1: ManimGL imports.** `from manimlib.imports import *` → wrong library. **RULE: ALWAYS `from manim import *`.**

**FM-E2: Deprecated names.** `TextMobject` → `Tex`, `TexMobject` → `MathTex`, `ShowCreation` → `Create`, `FadeInFromDown` → `FadeIn(mob, shift=DOWN)`.

**FM-E3: API hallucination.** #1 failure per TheoremExplainAgent (ACL 2025). LLMs invent nonexistent functions/parameters. **RULE: Include verified method whitelist in system prompt.**

**FM-E4: Missing voiceover imports.** `VoiceoverScene` is NOT in `from manim import *`. **RULE: Always add explicit voiceover imports.**

### Category F: Code structure errors

**FM-F1: Code outside `construct()`.** Animation at module level or in `__init__` fails. **RULE: ALL scene code inside `def construct(self):`.**

**FM-F2: Zero/negative `self.wait()`.** Can cause rendering errors. **RULE: Duration must be positive.**

---

## The Helper Library (tools.py) — v4, Manim v0.20.1 Correct

```python
"""
backend/manim_helpers/tools.py — v4
12 core functions. Each independently tested on Manim v0.20.1.
The LLM should prefer these over raw Manim.
"""
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService


# ── Text helpers (overflow-safe) ──────────────────────────────────

def safe_text(content: str, **kwargs) -> Text:
    """Create Text that won't overflow the frame."""
    t = Text(content, **kwargs)
    if t.width > config.frame_width - 2:
        t.scale_to_fit_width(config.frame_width - 2)
    return t


def safe_mathtex(tex_string: str, **kwargs) -> MathTex:
    """Create MathTex (math mode only, raw string) with overflow protection."""
    m = MathTex(tex_string, **kwargs)
    if m.width > config.frame_width - 2:
        m.scale_to_fit_width(config.frame_width - 2)
    return m


def show_title(text: str, subtitle: str = None) -> VGroup:
    """Animated title card with optional subtitle."""
    title = safe_text(text, font_size=48, color=WHITE)
    group = VGroup(title)
    if subtitle:
        sub = safe_text(subtitle, font_size=28, color=GRAY_B)
        sub.next_to(title, DOWN, buff=0.4)
        group.add(sub)
    group.move_to(ORIGIN)
    return group


# ── Axes and plotting ─────────────────────────────────────────────

def create_axes(
    x_range: tuple = (-4, 4, 1),
    y_range: tuple = (-3, 3, 1),
    x_label: str = "x",
    y_label: str = "y",
    x_length: float = 6,
    y_length: float = 4,
) -> VGroup:
    """Clean labeled axes with v0.20-correct defaults."""
    axes = Axes(
        x_range=x_range,
        y_range=y_range,
        x_length=x_length,
        y_length=y_length,
        axis_config={"include_numbers": True, "font_size": 24},
        tips=True,
    )
    labels = axes.get_axis_labels(
        Text(x_label, font_size=24),
        Text(y_label, font_size=24),
    )
    return VGroup(axes, labels)


def plot_function(axes: Axes, func, color=BLUE, x_range=None):
    """Plot a function on Axes."""
    plot_range = x_range or [axes.x_range[0] + 0.5, axes.x_range[1] - 0.5]
    return axes.plot(func, x_range=plot_range, color=color, stroke_width=3)


def animate_dot_along_curve(
    scene, axes: Axes, func, x_start: float, x_end: float,
    duration: float = 3.0, color=YELLOW,
):
    """Animate a dot tracing a curve. Returns the dot."""
    dot = Dot(axes @ (x_start, func(x_start)), color=color, radius=0.12)
    scene.play(FadeIn(dot, scale=2), run_time=0.3)
    curve_path = axes.plot(func, x_range=[x_start, x_end])
    scene.play(MoveAlongPath(dot, curve_path), run_time=duration - 0.3, rate_func=smooth)
    return dot


# ── Diagram helpers ───────────────────────────────────────────────

def labeled_box(
    text_str: str, color=BLUE, width: float = 3, height: float = 0.8,
    font_size: int = 24, fill_opacity: float = 0.3,
) -> VGroup:
    """Labeled rectangle for diagrams. Uses Text, not MathTex."""
    box = Rectangle(width=width, height=height, color=color, fill_opacity=fill_opacity,
                    fill_color=color)
    label = Text(text_str, font_size=font_size).move_to(box)
    return VGroup(box, label)


def connect_with_arrow(source, target, buff: float = 0.1, color=WHITE, label: str = None) -> VGroup:
    """Arrow from source bottom to target top with optional label."""
    arrow = Arrow(source.get_bottom(), target.get_top(), buff=buff, color=color, stroke_width=3)
    group = VGroup(arrow)
    if label:
        lbl = Text(label, font_size=20, color=color)
        lbl.next_to(arrow, RIGHT, buff=0.1)
        group.add(lbl)
    return group


def highlight_box(mobject, color=YELLOW, buff: float = 0.1, corner_radius: float = 0.1):
    """SurroundingRectangle with v0.20-correct keyword args (no positional args)."""
    return SurroundingRectangle(mobject, color=color, buff=buff, corner_radius=corner_radius)


def staggered_reveal(scene, mobjects, shift=RIGHT * 0.5, lag_ratio: float = 0.15, run_time: float = 2.0):
    """Reveal a list of mobjects with staggered FadeIn."""
    scene.play(LaggedStart(
        *[FadeIn(m, shift=shift) for m in mobjects],
        lag_ratio=lag_ratio, run_time=run_time,
    ))


# ── Code display ──────────────────────────────────────────────────

def code_block(code_str: str, language: str = "python", style: str = "monokai"):
    """Code display mobject using v0.19+ API (NOT the old file_name/style/insert_line_no params)."""
    return Code(
        code_string=code_str,
        language=language,
        formatter_style=style,
        add_line_numbers=True,
        paragraph_config={"font_size": 20, "font": "Monospace"},
        background_config={"corner_radius": 0.2, "buff": 0.3, "fill_opacity": 1},
    )


# ── Voiceover setup ───────────────────────────────────────────────

def setup_voiceover(scene: VoiceoverScene, voice_name: str = "Adam", use_bookmarks: bool = True):
    """Standard voiceover initialization. Always call this first in construct()."""
    kwargs = dict(
        voice_name=voice_name,
        voice_settings={"stability": 0.5, "similarity_boost": 0.75},
    )
    if use_bookmarks:
        kwargs["transcription_model"] = "base"
    scene.set_speech_service(ElevenLabsService(**kwargs))


# ── Scene utilities ───────────────────────────────────────────────

def fade_out_all(scene, duration: float = 0.5):
    """Fade out everything on screen between segments."""
    if scene.mobjects:
        scene.play(*[FadeOut(m) for m in scene.mobjects], run_time=duration)
```

### Rules for the helper library

1. Every function uses `Text()` by default, not `MathTex()`. LaTeX only for real equations.
2. Every function must be independently render-tested before adding.
3. `safe_text()` and `safe_mathtex()` are the highest-priority helpers — they prevent the most common visual bug (overflow).
4. Use `ax @ (x, y)` shorthand (v0.20 idiom) instead of `ax.c2p(x, y)`.
5. `highlight_box()` wraps `SurroundingRectangle` with keyword-only args (v0.19 breaking change).
6. `setup_voiceover()` handles the `transcription_model` footgun — always use it.
7. Add new helpers only when the LLM writes raw Manim that works well and is reusable.

---

## System Prompts

### 1. Coder System Prompt (most critical)

```markdown
You are a Manim code generator for Manim Community v0.20.1.
You write Python scene classes that extend VoiceoverScene from manim-voiceover.

## Environment
- Manim Community v0.20.1
- manim-voiceover v0.3.7 with ElevenLabs (pinned: elevenlabs==0.2.27)
- Python 3.10+

## Helper Library
You have access to pre-tested helper functions. ALWAYS prefer these over raw Manim:

{function_signatures_and_docstrings}

## IMPORTS (mandatory, exact)
```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService
from manim_helpers.tools import (
    setup_voiceover, safe_text, safe_mathtex, show_title,
    create_axes, plot_function, animate_dot_along_curve,
    labeled_box, connect_with_arrow, highlight_box,
    staggered_reveal, code_block, fade_out_all
)
```
NEVER use: manimlib, TextMobject, TexMobject, ShowCreation, CONFIG dicts

## SCENE STRUCTURE
- Exactly ONE class per file inheriting from VoiceoverScene
- All animation code inside def construct(self):
- FIRST line of construct: setup_voiceover(self)
- LAST line of construct: self.wait(0.5)

## LATEX RULES
- ALL LaTeX strings MUST use raw strings: r"..."
- MathTex = math mode only. NEVER put plain text in MathTex.
- Text = plain text only. NEVER put LaTeX commands in Text.
- Tex = LaTeX text mode. Use $...$ for inline math.
- Only amsmath and amssymb available by default.
- Every MathTex string argument must be brace-balanced.
- Use {{ }} ONLY for TransformMatchingTex submobject isolation.
- Prefer safe_mathtex() over raw MathTex() to prevent overflow.

## POSITIONING
- Frame: width ≈ 14.22, height = 8.0. Center = ORIGIN.
- Safe area: X ∈ [-6.5, 6.5], Y ∈ [-3.5, 3.5].
- ALWAYS position objects explicitly. Never leave multiple objects at ORIGIN.
- For potentially long text: use safe_text() or safe_mathtex().
- Use relative positioning (next_to, arrange, to_edge) over hardcoded coordinates.
- NEVER use pixel values as coordinates.
- Max 5-6 objects on screen at any time.

## ANIMATION RULES
- For rotations ≥ 90°: use Rotate(mob, angle), NOT mob.animate.rotate(angle)
- After Transform(A, B): reference A in subsequent animations.
- After ReplacementTransform(A, B): reference B in subsequent animations.
- Objects must be in scene (via self.add or creation anim) before animating.
- Chain .animate calls: mob.animate.shift(RIGHT).scale(2) — NOT separate .animate calls.
- Always specify run_time explicitly.
- Prefer FadeIn(mob, shift=UP) over bare FadeIn(mob) for polish.
- Use LaggedStart (or staggered_reveal helper) for lists/groups.
- Use GrowArrow for arrows, not Create.

## VOICEOVER TIMING
- NEVER use tracker.duration for more than one animation per voiceover block.
- For multiple animations: use bookmarks or tracker.get_remaining_duration().
- ALL synced animations must be INSIDE the with self.voiceover() block.
- Bookmark names: word characters only (letters, digits, underscores). No hyphens.
- Bookmark syntax: <bookmark mark='name'/>
- setup_voiceover(self) already sets transcription_model="base" — bookmarks work.

## CODE MOBJECT (v0.19+ API — old API will throw TypeError)
- Use code_block() helper. It wraps the new API correctly.
- If writing Code() directly: use code_string=, formatter_style=, add_line_numbers=
- NEVER use: file_name=, code=, style=, insert_line_no= (all renamed in v0.19)

## SURROUNDINGRECTANGLE (v0.19+ — no positional args)
- Use highlight_box() helper. It wraps correctly.
- If writing directly: SurroundingRectangle(mob, color=RED, buff=0.3) — keyword args only.

## AXES SHORTHAND (v0.20 idiom)
- Use ax @ (x, y) instead of ax.c2p(x, y) or ax.coords_to_point(x, y)

## VERIFIED MOBJECT METHODS (use only these):
shift(), move_to(), next_to(), to_edge(), to_corner(), scale(), scale_to_fit_width(),
set_color(), set_fill(), set_stroke(), set_opacity(), rotate(), arrange(),
arrange_in_grid(), get_center(), get_width(), get_height(), copy(), align_to(),
add_updater(), set_z_index(), get_top(), get_bottom(), get_left(), get_right(),
width (property), height (property), always.next_to() (v0.20 persistent updater)

## CREATION / REMOVAL ANIMATIONS
| Object type        | Create              | Remove               |
|--------------------|---------------------|----------------------|
| Geometric shapes   | Create(mob)         | FadeOut(mob)         |
| Text / Equations   | Write(mob)          | FadeOut(mob)         |
| Any (polished)     | FadeIn(mob,shift=UP)| FadeOut(mob,shift=DOWN)|
| Arrows             | GrowArrow(mob)      | FadeOut(mob)         |
| Groups / lists     | staggered_reveal()  | LaggedStart FadeOuts |

## RATE FUNCTIONS
| Effect                  | Rate function     |
|-------------------------|-------------------|
| Default smooth motion   | smooth            |
| Constant speed (Write)  | linear            |
| Object arriving         | rush_from         |
| Object departing        | rush_into         |
| Emphasis pulse          | there_and_back    |

## Few-shot examples
{paste_few_shot_examples_here}

## Lesson Plan:
{lesson_json}

Generate ONLY the Python code. No explanation, no markdown fences.
```

### 2. Planner System Prompt

```markdown
You are a curriculum designer for short animated explainer videos using Manim.

Given a topic, audience, and duration, produce a structured lesson plan as JSON.

Rules:
- 2-5 segments, each 10-25 seconds
- Each segment has ONE clear learning goal
- Narration is conversational, uses "you" and "we"
- For each visual element, specify text_classes: "Text" for plain, "MathTex" for math only, "Tex" for mixed
- For each visual element, specify position: "top", "center", "left", "right", "bottom-left", etc.
- Visual intent uses only these primitives:
  text, formula, axes, curve, dot, arrow, highlight, shape, box_diagram, number_line, transform
- Show visuals AFTER (or simultaneously with) verbal explanation — NEVER before
- End with a brief summary or "aha moment"
- Maximum 5-6 visual elements per segment
- Suggest specific helper functions from tools.py where applicable

Output valid JSON matching this schema:
{lesson_plan_schema}
```

### 3. Pedagogy Check Prompt

```markdown
Review this lesson plan for a {duration}-second animated explainer
targeting {audience} learners.

Check for:
1. Is any segment trying to cover too much? (each segment: ONE idea)
2. Are visuals shown before they're explained verbally? (explain first, then show)
3. Is the pacing appropriate for the audience level?
4. Does the flow follow: setup → concept → example → summary?
5. Will the narration sound natural when spoken aloud?
6. Are text_classes correct? (Text for plain text, MathTex for pure math, Tex for mixed)
7. Are positions specified to avoid objects stacking at ORIGIN?
8. Is any segment over 25 seconds? (split it if so)

If issues found: return the corrected JSON.
If plan is good: return it unchanged with "approved": true.
```

### 4. Repair System Prompt

```markdown
The following Manim v0.20.1 scene code failed to render with this error:

```
{traceback}
```

Original code:
```python
{original_code}
```

Diagnose and fix the error. Common causes ranked by frequency:
1. API hallucination (invented function/parameter name) — check verified methods list
2. LaTeX error — missing r"" prefix, unbalanced braces, text in MathTex
3. Positioning error — objects off-screen or stacked at ORIGIN
4. Timing error — tracker.duration used for multiple animations
5. Wrong base class — must be VoiceoverScene, not Scene
6. Deprecated API — see v0.18→v0.20 breaking changes

Return ONLY the corrected Python code. No explanation, no markdown fences.
```

---

## Few-Shot Examples for Coder Prompt

These three examples cover the most common scene types. Paste these into `{paste_few_shot_examples_here}`.

### Example 1: Math derivation with bookmarks

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService
from manim_helpers.tools import setup_voiceover, safe_mathtex, fade_out_all

class QuadraticFormula(VoiceoverScene):
    def construct(self):
        setup_voiceover(self)

        with self.voiceover(
            text="Let's derive the quadratic formula. "
                 "<bookmark mark='eq'/>We start with a x squared plus b x plus c equals zero. "
                 "<bookmark mark='result'/>The solution involves a square root."
        ) as tracker:
            self.wait_until_bookmark("eq")
            eq1 = MathTex(r"{{a}}x^2 + {{b}}x + {{c}} = 0")
            eq1.set_color_by_tex_to_color_map({"a": BLUE, "b": GREEN, "c": RED})
            eq1.move_to(ORIGIN)
            self.play(Write(eq1), run_time=tracker.time_until_bookmark("result"))

            self.wait_until_bookmark("result")
            result = safe_mathtex(r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}")
            result.next_to(eq1, DOWN, buff=0.8)
            self.play(FadeIn(result, shift=UP), run_time=tracker.get_remaining_duration())

        fade_out_all(self)
        self.wait(0.5)
```

### Example 2: Data visualization with animated dot

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService
from manim_helpers.tools import setup_voiceover, create_axes, plot_function, fade_out_all

class GrowthChart(VoiceoverScene):
    def construct(self):
        setup_voiceover(self)

        ax_group = create_axes(x_range=[0, 5, 1], y_range=[0, 25, 5],
                               x_label="t", y_label="f(t)")
        ax = ax_group[0]  # Axes object is first in VGroup

        with self.voiceover(
            text="<bookmark mark='axes'/>Here are our axes. "
                 "<bookmark mark='graph'/>Watch how the quadratic function grows. "
                 "<bookmark mark='dot'/>This dot traces the curve."
        ) as tracker:
            self.wait_until_bookmark("axes")
            self.play(Create(ax_group), run_time=tracker.time_until_bookmark("graph"))

            self.wait_until_bookmark("graph")
            graph = ax.plot(lambda t: t**2, color=BLUE)
            self.play(Create(graph), run_time=tracker.time_until_bookmark("dot"))

            self.wait_until_bookmark("dot")
            dot = Dot(color=YELLOW).move_to(ax @ (0, 0))
            self.play(FadeIn(dot, scale=0.5), run_time=0.3)
            self.play(MoveAlongPath(dot, graph),
                      run_time=tracker.get_remaining_duration())

        fade_out_all(self)
        self.wait(0.5)
```

### Example 3: Flowchart / pipeline diagram

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService
from manim_helpers.tools import setup_voiceover, labeled_box, connect_with_arrow, fade_out_all

class PipelineFlowchart(VoiceoverScene):
    def construct(self):
        setup_voiceover(self)

        step1 = labeled_box("Input", color=GREEN)
        step2 = labeled_box("Process", color=BLUE)
        step3 = labeled_box("Output", color=RED)
        steps = VGroup(step1, step2, step3).arrange(DOWN, buff=1.2)

        arrow1 = connect_with_arrow(step1, step2)
        arrow2 = connect_with_arrow(step2, step3)

        with self.voiceover(
            text="Here is our pipeline. <bookmark mark='s1'/>Data enters the input stage. "
                 "<bookmark mark='a1'/>It flows to processing. "
                 "<bookmark mark='s2'/>The process transforms the data. "
                 "<bookmark mark='a2'/>And finally, <bookmark mark='s3'/>we get the output."
        ) as tracker:
            self.wait_until_bookmark("s1")
            self.play(FadeIn(step1, shift=DOWN), run_time=0.7)
            self.wait_until_bookmark("a1")
            self.play(GrowArrow(arrow1), run_time=0.5)
            self.wait_until_bookmark("s2")
            self.play(FadeIn(step2, shift=DOWN), run_time=0.7)
            self.wait_until_bookmark("a2")
            self.play(GrowArrow(arrow2), run_time=0.5)
            self.wait_until_bookmark("s3")
            self.play(FadeIn(step3, shift=DOWN),
                      run_time=tracker.get_remaining_duration())

        fade_out_all(self)
        self.wait(0.5)
```

---

## Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                     │
│                     Next.js (Cloudflare Pages)                      │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │ Prompt Input │  │ Progress UI  │  │ Video Player + Download    │ │
│  │ + Settings   │  │ (polling 3s) │  │ (streams from R2)         │ │
│  └──────┬──────┘  └──────▲───────┘  └────────────▲──────────────┘ │
└─────────┼────────────────┼────────────────────────┼─────────────────┘
          │                │                        │
          ▼                │                        │
┌─────────────────────────────────────────────────────────────────────┐
│                   THIN API LAYER                                     │
│           FastAPI on Modal (or Cloudflare worker API routes)        │
│                                                                     │
│  POST /api/generate  →  triggers Modal function  →  returns job_id  │
│  GET  /api/status/:id →  reads job status                          │
│  GET  /api/video/:id  →  returns R2 video URL                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    MODAL (Serverless Containers)                     │
│                                                                     │
│  Image: manimcommunity/manim:v0.20.1                                │
│       + manim-voiceover[elevenlabs]                                 │
│       + elevenlabs==0.2.27  ← CRITICAL VERSION PIN                 │
│       + anthropic, boto3, pydantic>=2.0                             │
│                                                                     │
│  timeout=300, gpu=None (Manim is CPU-bound)                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Modal Setup

```python
# backend/modal_app.py
import modal

image = (
    modal.Image.from_registry("manimcommunity/manim:v0.20.1")
    .pip_install(
        "manim-voiceover[elevenlabs]",
        "elevenlabs==0.2.27",          # CRITICAL: current SDK breaks manim-voiceover
        "anthropic",
        "boto3",
        "pydantic>=2.0",
    )
    .copy_local_dir("./manim_helpers", "/app/manim_helpers")
    .copy_local_dir("./prompts", "/app/prompts")
)

app = modal.App("manimator", image=image)

@app.function(
    timeout=300,
    secrets=[
        modal.Secret.from_name("anthropic-key"),
        modal.Secret.from_name("elevenlabs-key"),
        modal.Secret.from_name("r2-credentials"),
    ],
)
def generate_video(prompt: str, duration: int = 60, audience: str = "beginner",
                   style: str = "3b1b", voice: str = "adam") -> dict:
    from pipeline.orchestrator import run_pipeline
    return run_pipeline(prompt=prompt, duration=duration,
                        audience=audience, style=style, voice=voice)

@app.function()
@modal.web_endpoint(method="POST")
def api_generate(request: dict):
    call = generate_video.spawn(**request)
    return {"job_id": call.object_id}

@app.function()
@modal.web_endpoint(method="GET")
def api_status(job_id: str):
    from modal.functions import FunctionCall
    call = FunctionCall.from_id(job_id)
    try:
        result = call.get(timeout=0)
        return {"status": "completed", **result}
    except TimeoutError:
        return {"status": "processing"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

---

## Project Structure

```
manimator/
├── .env.example
│
├── frontend/                          # Next.js (Cloudflare Pages / Vercel)
│   ├── app/
│   │   ├── page.tsx                   # prompt input
│   │   └── generate/[jobId]/page.tsx  # progress + video player
│   ├── components/
│   │   ├── PromptForm.tsx
│   │   ├── ProgressTracker.tsx
│   │   ├── VideoPlayer.tsx
│   │   └── StyleSelector.tsx
│   └── lib/
│       ├── api.ts
│       └── types.ts
│
├── backend/                           # Modal app
│   ├── modal_app.py
│   ├── requirements.txt               # includes elevenlabs==0.2.27
│   │
│   ├── pipeline/
│   │   ├── orchestrator.py            # runs all stages, updates progress
│   │   ├── planner.py                 # Stage 1: prompt → lesson JSON
│   │   ├── pedagogy.py                # Stage 2: quality check (optional)
│   │   ├── coder.py                   # Stage 3: lesson → VoiceoverScene code
│   │   └── uploader.py                # Stage 5: upload to R2
│   │
│   ├── manim_helpers/
│   │   ├── tools.py                   # 12 helpers, v0.20.1 correct
│   │   ├── styles.py                  # color presets / themes
│   │   └── templates/                 # few-shot examples for coder prompt
│   │       ├── quadratic_formula.py
│   │       ├── growth_chart.py
│   │       └── pipeline_flowchart.py
│   │
│   ├── prompts/
│   │   ├── planner_system.md
│   │   ├── pedagogy_system.md
│   │   ├── coder_system.md
│   │   └── repair_system.md
│   │
│   └── schemas/
│       ├── lesson.py                  # Pydantic: lesson plan
│       └── job.py                     # Pydantic: job status
│
└── tests/
    ├── test_helpers.py                # render test for each helper
    └── test_pipeline.py               # integration tests
```

---

## Build Schedule

### Day 1: Prove the Core Loop

**Goal:** Prompt → video file on your machine.

- [ ] `pip install "manim==0.20.1" "manim-voiceover[elevenlabs]" "elevenlabs==0.2.27" anthropic`
- [ ] Write all 12 tools.py helper functions
- [ ] Render test EACH helper individually (catch v0.20 API issues early)
- [ ] Write ONE complete VoiceoverScene by hand using helpers (use Example 1 as template)
- [ ] Verify it renders with ElevenLabs audio and audio is synced
- [ ] Implement `planner.py` (Claude API → lesson JSON)
- [ ] Implement `coder.py` (Claude API → VoiceoverScene code, using coder system prompt)
- [ ] Implement repair loop (render → catch traceback → retry up to 3×)
- [ ] Run end-to-end: `python orchestrator.py "explain binary search"`

**Exit criteria:** A `.mp4` file exists on your machine with synced narration.

### Day 2: Infrastructure + API

**Goal:** Pipeline runs in Modal, returns a video URL.

- [ ] Set up Modal account and CLI (`pip install modal && modal setup`)
- [ ] Define Modal image with `manimcommunity/manim:v0.20.1` + pinned elevenlabs
- [ ] Implement `modal_app.py` with `generate_video` function
- [ ] Set up Cloudflare R2 bucket + upload utility
- [ ] Implement web endpoints (POST /generate, GET /status)
- [ ] Deploy to Modal (`modal deploy modal_app.py`)
- [ ] Test: `curl -X POST` → poll status → get video URL
- [ ] Fix the 3 most common render failures from Day 1

**Exit criteria:** HTTP request → working video URL.

### Day 3: Frontend + Ship

**Goal:** Someone can visit your site and generate a video.

- [ ] Scaffold Next.js + Tailwind + shadcn/ui
- [ ] Build `PromptForm` component (prompt, duration, audience, style, voice)
- [ ] Build `ProgressTracker` (polling every 3s with stage display)
- [ ] Build `VideoPlayer` with download button
- [ ] Wire up API calls (`lib/api.ts`)
- [ ] Deploy to Cloudflare Pages / Vercel
- [ ] Test full flow end-to-end
- [ ] Fix CORS and deployment issues

**Exit criteria:** A live URL you can share.

### Week 2: Harden

- [ ] Run on 20 diverse prompts, catalog failures by category (A–F above)
- [ ] Add helpers for the raw Manim patterns that recur
- [ ] Add subtitle generation (`.srt` from narration text)
- [ ] Add style presets (3B1B dark theme, minimal light, colorful)
- [ ] Add rate limiting
- [ ] Add pedagogy check stage
- [ ] Add cost tracking per job
- [ ] Polish UI (loading animations, error states, retry button)
- [ ] Pre-rendered example gallery on landing page

---

## Environment Variables

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=https://your-app--manimator-api-generate.modal.run

# Modal secrets (set via `modal secret create <name> ANTHROPIC_API_KEY=...`)
# anthropic-key:
ANTHROPIC_API_KEY=sk-ant-...

# elevenlabs-key:
ELEVENLABS_API_KEY=...

# r2-credentials:
R2_ACCOUNT_ID=...
R2_ACCESS_KEY=...
R2_SECRET_KEY=...
R2_BUCKET=manimator-videos
R2_PUBLIC_URL=https://pub-xxx.r2.dev
```

---

## Cost Estimates

### Per video

| Component | Cost |
|-----------|------|
| Claude Sonnet (planner + coder + retries) | ~$0.05–0.15 |
| ElevenLabs TTS (60s, called during render) | ~$0.10–0.30 |
| Modal compute (~90s CPU container time) | ~$0.01 |
| Cloudflare R2 storage + serving | ~$0.001 |
| **Total** | **~$0.15–0.50** |

Note: Repair loop retries don't re-call ElevenLabs (audio cached). Only changed narration text costs additional TTS credits.

### Monthly infrastructure

| Service | Cost |
|---------|------|
| Cloudflare Pages (frontend) | Free |
| Modal | Pay-per-use ($0 when idle) |
| Cloudflare R2 | Free tier (10 GB) |
| ElevenLabs | $5–22/mo (Creator plan) |
| Claude API | Pay-as-you-go |
| **Total (light usage)** | **~$5–25/mo** |

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| ElevenLabs SDK version conflict | Pin `elevenlabs==0.2.27` in requirements.txt and Modal image |
| LLM generates bad Manim code | Repair loop (3 attempts) + failure-mode ruleset in system prompt + helper library |
| LaTeX compilation fails | Default to `Text()` everywhere; `MathTex()` only for real equations; FM-A ruleset |
| API hallucination (#1 failure) | Verified method whitelist in coder prompt; few-shot examples; helper library narrows surface |
| Objects off-screen or stacked | `safe_text()` / `safe_mathtex()` helpers; FM-D ruleset; position specs in lesson JSON |
| VoiceoverScene timing wrong | FM-C ruleset; Pattern 1/2/3 examples; `get_remaining_duration()` enforced |
| Modal cold start slow | ~10s first request, subsequent faster. Acceptable for v1. |
| Manim v0.20 breaking changes | Version pinned; Code/SurroundingRectangle helpers wrap new API |
| Videos cut off at the end | Always `self.wait(0.5)` as last line of `construct()` |

---

## What NOT to Build (V1)

- ❌ User accounts / auth
- ❌ Scene-level editing / regeneration (use `--save_sections` in v2)
- ❌ 3D Manim scenes
- ❌ Custom voice cloning
- ❌ Parallel scene rendering (v2 optimization)
- ❌ SSE for progress (polling is fine for v1)
- ❌ Payment / credits
- ❌ Mobile-optimized UI

---

## V2 Roadmap

1. **Parallel rendering:** Manim sections (`--save_sections`), each in separate Modal container, stitch with pyav/ffmpeg. 3–5× faster.
2. **Scene editor:** Show each segment with narration. User edits text or visual intent. Regenerate just that section.
3. **Gallery:** User accounts, saved videos, community browsing.
4. **Style transfer:** Specific color/animation presets per style.
5. **Batch mode:** Upload a syllabus, generate a course.
6. **Monetization:** Credits system, ~$0.50–1.00/video.

---

## TL;DR — The Seven Decisions That Matter

1. **VoiceoverScene, not custom audio sync** — collapses 3 pipeline stages into 0
2. **Modal, not Railway + Docker** — removes days of DevOps pain
3. **Helper library (tools.py)** — narrows LLM API surface; compound advantage that grows
4. **`Text()` over `MathTex()` by default** — eliminates the #1 render failure
5. **Repair loop** — assume code gen fails; build recovery into the system
6. **Pin `elevenlabs==0.2.27`** — current ElevenLabs SDK breaks manim-voiceover v0.3.7
7. **Failure-mode ruleset in coder prompt** — API hallucination is the #1 failure; constrain the surface

Everything else is details. Nail these seven and the project works.
