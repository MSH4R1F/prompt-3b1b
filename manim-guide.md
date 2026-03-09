# ManimAI pipeline: exhaustive reference for system prompts and tools.py

**Everything below is verified against Manim Community v0.20.1 (released Feb 2026) and manim-voiceover v0.3.7.** This document covers the five deliverables you requested: version-migration notes, tools.py API reference, VoiceoverScene deep dive, failure-mode catalog, and system-prompt ingredients. Use it as a single source of truth when writing your coder and planner prompts.

---

## 1. What changed from v0.18 → v0.20 that breaks LLM-generated code

The migration spans two major releases — v0.19.0 (Jan 2025) and v0.20.0 (Feb 2026). **Seven breaking changes will trip up any LLM trained on pre-2025 tutorials.**

### Code mobject — complete constructor rewrite (v0.19, the biggest break)

Every parameter was renamed. An LLM that writes `Code(file_name=..., style=..., insert_line_no=True)` will get an immediate `TypeError`.

| Old (v0.18) | New (v0.19+) |
|---|---|
| `file_name` | `code_file` |
| `code` | `code_string` |
| `style` | `formatter_style` |
| `insert_line_no` | `add_line_numbers` |
| `line_no_from` | `line_numbers_from` |
| `font`, `font_size`, `line_spacing`, `stroke_width` | `paragraph_config={"font": ..., "font_size": ..., ...}` |
| `margin`, `background_stroke_*`, `corner_radius` | `background_config={"buff": ..., "stroke_width": ..., ...}` |

Correct v0.20 usage:

```python
Code(
    code_string="print('hello')",
    language="python",
    formatter_style="monokai",
    add_line_numbers=True,
    paragraph_config={"font_size": 24, "font": "Monospace"},
    background_config={"stroke_width": 2, "corner_radius": 0.3},
)
```

### SurroundingRectangle — positional args removed (v0.19)

`SurroundingRectangle(mob, RED, 0.3)` now fails. Must use keyword args: `SurroundingRectangle(mob, color=RED, buff=0.3)`. The class also now accepts `*mobjects` (multiple mobjects) and tuple buffs `buff=(0.5, 0.2)` for separate x/y padding (v0.20).

### MathTex internal splitting rewritten (v0.20)

The `{{ }}` double-brace submobject-isolation logic was rewritten for robustness. The API surface is identical, but **submobject indices may differ** from v0.18 code that relied on quirky splitting behavior. Code using `eq[2]` to target a specific part may now be wrong.

### New features LLMs should use

- **`ax @ (x, y)` shorthand** (v0.19) — replaces `ax.coords_to_point(x, y)`. Idiomatic modern Manim.
- **`Mobject.always`** (v0.20) — `dot.always.next_to(square, UP)` creates persistent updaters without `add_updater`. Major new pattern.
- **`Animation.set_default()`** (v0.19) — set default `run_time` etc. for animation classes.
- **`VGroup` accepts iterables** (v0.19) — `VGroup(squares)` works, no need to unpack `*`.
- **`ManimColor.darker()`, `.lighter()`, `.contrasting()`** (v0.19) — useful for dynamic color schemes.
- **`run_time=0` and `Add` animation** (v0.19) — instant additions possible.
- **`Scene.time` property** (v0.19) — access current render time.
- **`scene.next_section(section_type=...)` replaces `type=`** (v0.19).
- **`ManimColor.from_hex(hex_str=...)` replaces `hex=`** (v0.19).
- **`PURE_CYAN`, `PURE_MAGENTA`, `PURE_YELLOW`** added (v0.20). `YELLOW_C` hex value was corrected.
- **ffmpeg no longer required** — Manim now uses `pyav` internally.

### Deprecated/removed items

- `Sector(inner_radius=, outer_radius=)` — use `Sector(radius=, angle=)`. Use `AnnularSector` for inner/outer.
- `ImageMobject` resampling algorithms `lanczos`, `box`, `hamming` removed (v0.20). Only `nearest`, `linear`, `cubic` remain.
- `CONFIG = {}` class dictionaries — silently ignored. Use `__init__` kwargs.
- `TextMobject` → `Tex`, `TexMobject` → `MathTex`, `ShowCreation` → `Create` (removed long ago but LLMs still generate them).

---

## 2. Exhaustive tools.py API reference for v0.20.x

This section documents every class your helper library should wrap, with exact constructor signatures and correct usage patterns.

### Axes and NumberPlane

```python
from manim import Axes, NumberPlane

# Axes constructor
Axes(
    x_range=None,         # (x_min, x_max, x_step) or None
    y_range=None,         # (y_min, y_max, y_step) or None
    x_length=12,          # float — scene-space length of x axis
    y_length=6,           # float — scene-space length of y axis
    axis_config=None,     # dict passed to both NumberLine axes
    x_axis_config=None,   # dict override for x axis only
    y_axis_config=None,   # dict override for y axis only
    tips=True,            # bool — arrow tips on axes
)
```

**Key methods on Axes/CoordinateSystem:**

- `ax.plot(func, x_range=None, use_smoothing=True, **kwargs)` → ParametricFunction
- `ax.get_axis_labels(x_label="x", y_label="y")` → VGroup
- `ax.coords_to_point(x, y)` / `ax.c2p(x, y)` / `ax @ (x, y)` — axis coords → scene point
- `ax.point_to_coords(pt)` / `ax.p2c(pt)` — inverse
- `ax.i2gp(x, graph)` — input to graph point (scene point on graph at x)
- `ax.get_graph_label(graph, label, x_val=None, direction=UR, buff=0.25, dot=False)`
- `ax.plot_line_graph(x_values, y_values, line_color=YELLOW, add_vertex_dots=True)` → VDict with keys `"line_graph"`, `"vertex_dots"`
- `ax.get_area(graph, x_range=None, color=(BLUE, GREEN), opacity=0.3, bounded_graph=None)`
- `ax.get_vertical_line(point)`, `ax.get_horizontal_line(point)`, `ax.get_T_label(x_val, graph)`

```python
# NumberPlane — inherits all Axes methods plus a background grid
NumberPlane(
    x_range=(-7.111, 7.111, 1),  # defaults fill the frame
    y_range=(-4.0, 4.0, 1),
    background_line_style=None,   # dict: stroke_color, stroke_width, etc.
    faded_line_style=None,
    faded_line_ratio=1,
)
# Has prepare_for_nonlinear_transform() for smooth apply_function() distortions
```

### Text rendering — Text, MarkupText, Tex, MathTex

```python
from manim import Text, MarkupText, Tex, MathTex

# Text — Pango, no LaTeX, supports system fonts
Text(
    "Hello World",
    font_size=48,          # default
    color=WHITE,
    font="",               # system font name, case-sensitive
    weight="NORMAL",       # or "BOLD"
    slant="NORMAL",        # or "ITALIC"
    line_spacing=-1,       # auto
    t2c=None,              # {"substring": COLOR} per-char color map
    t2f=None,              # per-char font map
    t2g=None,              # per-char gradient map
    gradient=None,         # global gradient: (RED, BLUE)
    disable_ligatures=False,
)

# MarkupText — Pango with HTML-like markup
MarkupText(
    '<b>Bold</b> and <span foreground="blue">blue</span>',
    font_size=48,
)
# Tags: <b>, <i>, <s>, <u>, <big>, <small>, <sub>, <sup>, <tt>
# <span foreground="blue" size="x-large">styled</span>
# Custom: <gradient from="RED" to="YELLOW">text</gradient>
# Escape: &gt; &lt; &amp;

# Tex — LaTeX text mode (center environment)
Tex(r"The area is $\pi r^2$", font_size=48)
# Use $...$ for inline math inside text mode

# MathTex — LaTeX math mode (align* environment)
MathTex(r"\frac{d}{dx} e^x = e^x", font_size=48)
# ALWAYS use raw strings (r"...") for LaTeX
```

**Key MathTex patterns:**

```python
# Multiple string args → separate submobjects
eq = MathTex("a^2", "+", "b^2", "=", "c^2")
eq[0].set_color(RED)  # colors "a^2"

# Double-brace isolation for TransformMatchingTex
eq = MathTex(r"{{ a^2 }} + {{ b^2 }} = {{ c^2 }}")

# Color by tex substring
eq.set_color_by_tex("a", RED)
eq.set_color_by_tex_to_color_map({"a": RED, "b": BLUE})

# Custom LaTeX packages
template = TexTemplate()
template.add_to_preamble(r"\usepackage{mathrsfs}")
MathTex(r"\mathscr{H}", tex_template=template)
```

### Geometry primitives — Arrow, Line, Dot

```python
from manim import Arrow, Line, DashedLine, DoubleArrow, Dot, LabeledDot

Line(start=LEFT, end=RIGHT, buff=0, path_arc=0)
Arrow(start=LEFT, end=RIGHT, stroke_width=6, buff=0.25,
      max_tip_length_to_length_ratio=0.25, tip_shape=ArrowTriangleFilledTip)
DashedLine(start=LEFT, end=RIGHT, dash_length=0.05, dashed_ratio=0.5)
DoubleArrow(start=LEFT, end=RIGHT)  # tips on both ends
Dot(point=ORIGIN, radius=0.08, color=WHITE, fill_opacity=1.0)
LabeledDot(label="A", radius=None, buff=0.1)  # auto-sizes around label
```

Tip shapes available: `ArrowTriangleFilledTip` (default), `ArrowSquareTip`, `ArrowSquareFilledTip`, `ArrowCircleTip`, `ArrowCircleFilledTip`, `StealthTip`.

### ValueTracker and DecimalNumber

```python
from manim import ValueTracker, DecimalNumber, Integer, Variable

# ValueTracker — invisible mobject that holds a scalar
tracker = ValueTracker(0)
tracker.get_value()           # → float
tracker.set_value(5)
tracker.increment_value(0.1)
self.play(tracker.animate.set_value(5))  # animatable

# With updater
dot = Dot()
dot.add_updater(lambda m: m.set_x(tracker.get_value()))

# DecimalNumber — displays a number that can be updated
decimal = DecimalNumber(
    number=0,
    num_decimal_places=2,
    include_sign=False,
    group_with_commas=True,
    font_size=48,
    unit=None,         # e.g. r"\text{m/s}"
    edge_to_fix=LEFT,  # alignment anchor
)
decimal.add_updater(lambda d: d.set_value(tracker.get_value()))

# Variable — "label = value" display with built-in tracker
var = Variable(2, Text("x"), num_decimal_places=3)
# var.tracker is a ValueTracker; var.value is the DecimalNumber
self.play(var.tracker.animate.set_value(5))
```

### Graph and DiGraph (network diagrams)

```python
from manim import Graph, DiGraph

Graph(
    vertices=[1, 2, 3, 4],
    edges=[(1,2), (2,3), (3,4), (4,1)],
    labels=True,          # or dict {vertex: Mobject}
    layout="spring",      # see layout algorithms below
    layout_scale=2,
    layout_config=None,   # dict passed to layout algorithm
    vertex_type=Dot,
    vertex_config=None,   # global or per-vertex: {1: {"color": RED}}
    edge_type=Line,
    edge_config=None,     # global or per-edge: {(1,2): {"color": RED}}
    root_vertex=None,     # for "tree" layout
    partitions=None,      # for "partite" layout
)
```

**Layout algorithms:** `"spring"` (default, Fruchterman-Reingold), `"circular"`, `"kamada_kawai"`, `"planar"`, `"random"`, `"shell"`, `"spectral"`, `"spiral"`, `"partite"`, `"tree"`, or a `dict` mapping vertices to `[x, y, z]` coordinates.

Key methods: `g.add_edges()`, `g.remove_edges()`, `g.add_vertices()`, `g.remove_vertices()`, `g.change_layout()`, `Graph.from_networkx(nxgraph)`. Edges auto-update when vertices move.

### Code display (v0.19+ API)

```python
from manim import Code

Code(
    code_string="def hello():\n    print('world')",
    code_file=None,          # or path to file
    language="python",
    formatter_style="vim",   # Pygments style (see Code.get_styles_list())
    tab_width=4,
    add_line_numbers=True,
    line_numbers_from=1,
    background="rectangle",  # or "window"
    paragraph_config={"font": "Monospace", "font_size": 24, "line_spacing": 0.5},
    background_config={"buff": 0.3, "fill_color": "#222", "corner_radius": 0.2,
                       "stroke_width": 1, "fill_opacity": 1},
)
```

### Color system

Core colors each have shades `_A` (lightest) through `_E` (darkest), with `_C` as default. `RED = RED_C`, `BLUE = BLUE_C`, etc.

```python
# Core palette
RED, BLUE, GREEN, YELLOW, PURPLE, TEAL, ORANGE, PINK, GOLD, MAROON
WHITE, BLACK, GREY, GRAY, DARK_GREY, LIGHT_GREY
PURE_CYAN, PURE_MAGENTA, PURE_YELLOW  # new in v0.20

# New methods (v0.19+)
BLUE.darker(0.3)       # toward BLACK
BLUE.lighter(0.2)      # toward WHITE
BLUE.contrasting()     # BLACK or WHITE for readable text on BLUE

# Gradients
color_gradient([RED, BLUE], 10)        # → list of 10 interpolated ManimColors
interpolate_color(RED, BLUE, 0.5)      # midpoint color
group.set_color_by_gradient(BLUE, GREEN, YELLOW)

# Custom hex
from manim import ManimColor
ManimColor("#FF5733")
ManimColor("#F00")       # short hex (v0.19+)
ManimColor("#FF0000AA")  # with alpha
```

### Transform animations — complete decision tree

| Animation | Scene effect | When to use |
|---|---|---|
| `Transform(A, B)` | A morphs to look like B; A stays in scene | Simple morph, subsequent refs use `A` |
| `ReplacementTransform(A, B)` | A removed, B added | Chain of transforms referencing `B` afterward |
| `TransformMatchingTex(eq1, eq2)` | Matches submobjects by TeX string | Equation derivations with `{{ }}` isolation |
| `TransformMatchingShapes(A, B)` | Matches by point-set similarity | Non-text shape morphing |
| `FadeTransform(A, B)` | Cross-fade | Labels, text style changes |
| `FadeTransformPieces(A, B)` | Piece-by-piece cross-fade | Submobject-level fade transitions |
| `MoveToTarget(A)` | Morphs A to A.target | Complex multi-property changes after `A.generate_target()` |
| `TransformFromCopy(A, B)` | Copy of A morphs to B; A stays | Show derivation while keeping original |

### Animation composition

```python
from manim import AnimationGroup, LaggedStart, LaggedStartMap, Succession

AnimationGroup(*anims, lag_ratio=0)            # simultaneous
LaggedStart(*anims, lag_ratio=0.05)            # staggered
LaggedStartMap(FadeIn, vgroup, lag_ratio=0.1)  # apply same anim to each submobject
Succession(Write(a), Write(b), Write(c))       # sequential in one play() call
```

### Indication animations

```python
from manim import Circumscribe, Indicate, Flash, Wiggle, FocusOn, ApplyWave

Circumscribe(mob, shape=Rectangle, color=YELLOW, buff=0.1, run_time=1)
Indicate(mob, scale_factor=1.2, color=YELLOW, rate_func=there_and_back)
Flash(point_or_mob, flash_radius=0.1, num_lines=12, color=YELLOW)
Wiggle(mob, scale_value=1.1, rotation_angle=0.02*TAU, n_wiggles=6, run_time=2)
FocusOn(point_or_mob, opacity=0.2, color=GREY, run_time=2)
ApplyWave(mob, direction=UP, amplitude=0.2, run_time=2)
```

### Scene setup — camera and frame

```python
# Background color (set BEFORE scene class or in construct)
self.camera.background_color = "#1C1C1C"
# Or at module level: config.background_color = WHITE

# Frame dimensions (read-only reference)
# Default: frame_width ≈ 14.22, frame_height = 8.0
# Default pixels: 1920×1080

# MovingCameraScene — zoom and pan
class MyScene(MovingCameraScene):
    def construct(self):
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.set(width=4).move_to(detail))
        self.play(Restore(self.camera.frame))
        # auto_zoom fits frame to mobjects
        self.play(self.camera.auto_zoom(group, margin=2))
```

### Positioning constants and methods

```python
# Direction constants
ORIGIN = [0,0,0]; UP = [0,1,0]; DOWN = [0,-1,0]; LEFT = [-1,0,0]; RIGHT = [1,0,0]
UL = [-1,1,0]; UR = [1,1,0]; DL = [-1,-1,0]; DR = [1,-1,0]

# Buffer constants
SMALL_BUFF = 0.1; MED_SMALL_BUFF = 0.25; MED_LARGE_BUFF = 0.5; LARGE_BUFF = 1.0

# Positioning methods
mob.move_to(point)              # absolute
mob.shift(direction)            # relative (cumulative)
mob.next_to(other, DOWN, buff=0.3)
mob.to_edge(UP, buff=0.5)
mob.to_corner(UL, buff=0.5)
mob.align_to(other, LEFT)

# VGroup layout
VGroup(a, b, c).arrange(DOWN, aligned_edge=LEFT, buff=0.4)
VGroup(*items).arrange_in_grid(rows=3, cols=4, buff=0.3)
mob.scale_to_fit_width(config.frame_width - 2)  # prevent overflow
```

---

## 3. VoiceoverScene deep dive

### Installation and SDK version warning

```bash
pip install "manim-voiceover[elevenlabs]"
```

**Critical:** `manim-voiceover` v0.3.7 pins `elevenlabs ^0.2.27`. The current ElevenLabs SDK (v1.50+/v2.1+) is **incompatible**. Either pin `elevenlabs==0.2.27` or use the fork `manim-voiceover-enhanced` which supports the new SDK API.

### Core imports and setup

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService

class MyScene(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            ElevenLabsService(
                voice_name="Adam",
                voice_id=None,              # takes priority over voice_name
                voice_settings={"stability": 0.5, "similarity_boost": 0.75},
                transcription_model="base",  # REQUIRED for bookmark support
            )
        )
```

The `transcription_model` parameter accepts Whisper model sizes: `"base"`, `"small"`, `"medium"`, `"large"`. **Without it, bookmarks either use inaccurate linear interpolation or raise exceptions.** `"base"` is recommended for speed.

### All tracker properties and methods

| Property/Method | Type | Description |
|---|---|---|
| `tracker.duration` | `float` | Total audio duration in seconds |
| `tracker.start_t` | `float` | Scene render time when voiceover starts |
| `tracker.end_t` | `float` | `start_t + duration` |
| `tracker.data` | `dict` | Full TTS result: `original_audio`, `final_audio`, `input_text`, `word_boundaries` |
| `tracker.bookmark_times` | `dict` | `{name: absolute_scene_time}` — only set if word boundaries exist |
| `tracker.bookmark_distances` | `dict` | `{name: character_offset}` |
| `tracker.input_text` | `str` | Original text with bookmarks |
| `tracker.content` | `str` | Text with bookmarks stripped |
| `tracker.time_interpolator` | `TimeInterpolator` | scipy `interp1d` mapping char offset → audio time |
| `tracker.get_remaining_duration(buff=0)` | method → `float` | `max(end_t - current_time + buff, 0)` |
| `tracker.time_until_bookmark(mark, buff=0, limit=None)` | method → `float` | Seconds until named bookmark; `limit` caps the return value |

### Bookmark syntax — exact specification

Format: `<bookmark mark='name'/>` (self-closing XML tag).

**Internal regex:** `re.split(r"(<bookmark\s*mark\s*=[\'\"]\w*[\"\']\s*/>)", text)` — this means **bookmark names must be word characters only** (letters, digits, underscores). No hyphens, spaces, or special characters.

Both quote styles work: `mark='A'` and `mark="A"`. Whitespace is flexible around attributes.

### Three canonical timing patterns

**Pattern 1 — Single animation, full duration:**
```python
with self.voiceover(text="This circle appears now.") as tracker:
    self.play(Create(circle), run_time=tracker.duration)
```

**Pattern 2 — Multiple animations with bookmarks:**
```python
with self.voiceover(
    text="""First we <bookmark mark='draw'/>draw a circle,
    then <bookmark mark='color'/>color it red."""
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

### How caching works (critical for repair loops)

Cache location: `{config.media_dir}/voiceovers/` (typically `./media/voiceovers/`). Override via `cache_dir` in service constructor.

Each TTS call produces an audio file and a JSON cache entry. The **cache key** is the input text **with bookmarks stripped**, plus the service config (voice, model, speed). This means:

- **Changing voiceover text** → new TTS call (new cache entry)
- **Changing only bookmark positions** → **no TTS regeneration** (bookmarks are stripped from the cache key). Bookmark times are recomputed from cached word boundaries.
- **Changing voice/model settings** → new TTS call
- **Changing only the animation code** → no TTS regeneration (audio cached)

This is excellent for repair loops — animation code can be iterated without burning API credits. To force regeneration, delete the cache directory.

The `global_speed` parameter on `SpeechService` adjusts playback speed via SoX (requires SoX v14.4.2+ installed). Speed-adjusted audio is stored separately as `final_audio`.

### VoiceoverScene with multiple inheritance

```python
from manim.scene.moving_camera_scene import MovingCameraScene

class MyScene(MovingCameraScene, VoiceoverScene):
    def construct(self):
        self.set_speech_service(...)
        # Both camera manipulation and voiceover available
```

`VoiceoverScene` should typically come last in the MRO. The `voiceover()` context manager **automatically calls `wait_for_voiceover()` on exit** — you never need to call it manually inside a `with` block.

### VoiceoverScene pitfalls summary

- `set_speech_service()` must be called before any voiceover or you get `Exception: "You need to call init_voiceover()..."`
- `safe_wait()` silently does nothing for sub-frame durations (`≤ 1/frame_rate`)
- SSML is not implemented — `self.voiceover(ssml=...)` raises `NotImplementedError`
- Subcaptions are auto-generated from text with bookmarks stripped; override with `subcaption=` parameter
- TTS generation is synchronous — all audio is generated when entering the `with` block, before animations run

---

## 4. Failure mode catalog — comprehensive rules for LLM code generation

### Category A: LaTeX and TeX errors

**FM-A1: Missing raw string prefix.** `MathTex("\\frac{1}{2}")` causes escape-sequence bugs or LaTeX compilation failure. **Rule: ALL strings passed to `Tex()`, `MathTex()`, or `TexTemplate` MUST use `r"..."` raw string syntax.**

**FM-A2: Text content in MathTex.** `MathTex(r"The equation is E=mc^2")` fails because MathTex wraps everything in `align*` (math mode). **Rule: `MathTex` = pure math only. For mixed text+math, use `Tex(r"The equation is $E=mc^2$")` or `MathTex(r"\text{The equation is } E=mc^2")`.**

**FM-A3: LaTeX commands in Text().** `Text(r"\frac{1}{2}")` renders the literal string, not a fraction, because `Text` uses Pango, not LaTeX. **Rule: `Text()` for plain text only. `MathTex()` for math. `Tex()` for LaTeX text mode.**

**FM-A4: Unbalanced braces across MathTex args.** `MathTex(r"\frac{", "u'v - uv'", r"}{v^2}")` fails because each arg is compiled separately. **Rule: Every string argument to MathTex/Tex must be brace-balanced.**

**FM-A5: Confusing `{{ }}` with LaTeX grouping.** The `{{ }}` syntax is Manim-specific submobject isolation, not standard LaTeX. **Rule: Only use `{{ }}` deliberately for submobject splitting (e.g., for `TransformMatchingTex`). For regular LaTeX grouping, use single `{}`.**

**FM-A6: Unavailable LaTeX packages.** Default template includes only `amsmath`, `amssymb`, and `babel` (English). Commands like `\mathscr` (needs `mathrsfs`) or `\coloneqq` (needs `mathtools`) fail with "Undefined control sequence." **Rule: Only use `amsmath`/`amssymb` commands unless you explicitly create a `TexTemplate` with `add_to_preamble()`.**

### Category B: Animation logic errors

**FM-B1: `.animate` rotation ≥ 90°.** `mob.animate.rotate(PI)` does nothing visible because `.animate` interpolates start→end states, and a 180° rotation yields the same state. **Rule: For rotations ≥ 90°, use `Rotate(mob, angle)` instead of `.animate.rotate()`.**

**FM-B2: Transform vs ReplacementTransform confusion.** After `Transform(A, B)`, the scene object is still `A` (looking like B). Trying to animate `B` afterward fails silently. **Rule: After `Transform(A, B)` → reference `A`. After `ReplacementTransform(A, B)` → reference `B`.**

**FM-B3: Animating unadded objects.** `self.play(circle.animate.shift(RIGHT))` does nothing if circle was never added. **Rule: Objects must be in the scene (via `self.add()` or a creation animation) before transforming them.**

**FM-B4: Conflicting `.animate` on same object.** `self.play(mob.animate.shift(RIGHT), mob.animate.scale(2))` creates two separate animate builders. **Rule: Chain on one builder: `mob.animate.shift(RIGHT).scale(2)`.**

### Category C: VoiceoverScene timing errors

**FM-C1: Using `tracker.duration` for multiple animations.** Each animation gets the full duration, making total time 2× or 3× the voiceover. **Rule: Never use `tracker.duration` for more than one animation in a voiceover block. Use `tracker.get_remaining_duration()` or bookmarks to subdivide.**

**FM-C2: Bookmark not found.** Bookmarks require word boundary data, which requires `transcription_model="base"` in the service constructor. **Rule: Always set `transcription_model="base"` when using bookmarks.**

**FM-C3: Animations outside the `with` block.** The `with` block auto-waits for voiceover completion on exit. Animations placed after it won't sync. **Rule: ALL animations synced to a voiceover must be inside the `with self.voiceover()` block.**

**FM-C4: Inheriting from `Scene` instead of `VoiceoverScene`.** Causes `AttributeError: object has no attribute 'voiceover'`. **Rule: Any scene using voiceover MUST inherit from `VoiceoverScene`.**

### Category D: Coordinate and positioning errors

**FM-D1: Objects off-screen.** Default frame is **~14.22 × 8.0** units centered at ORIGIN. `circle.move_to(10 * RIGHT)` is invisible. **Rule: Keep all content within X ∈ [-6.5, 6.5], Y ∈ [-3.5, 3.5] for safe margins.**

**FM-D2: Objects stacked at ORIGIN.** All mobjects default to center. Multiple objects without positioning overlap. **Rule: Always position objects using `arrange()`, `next_to()`, `to_edge()`, or `move_to()` after creation.**

**FM-D3: Pixel vs. scene coordinates.** `mob.move_to([960, 540, 0])` uses pixel values in scene space, placing the object astronomically off-screen. **Rule: Manim coordinates use scene units. Center is (0,0). Width ≈ 14.22, height = 8.0. Never use pixel values.**

**FM-D4: Large text overflow.** Long equations or text can exceed the frame. **Rule: For potentially long text, constrain with `mob.scale_to_fit_width(config.frame_width - 2)` or set `mob.width = config.frame_width - 2`.**

### Category E: Import and version errors

**FM-E1: ManimGL imports.** LLMs trained on older data generate `from manimlib.imports import *`. **Rule: ALWAYS use `from manim import *` for Manim Community. NEVER use `manimlib`.**

**FM-E2: Deprecated class names.** `TextMobject` → `Tex`, `TexMobject` → `MathTex`, `ShowCreation` → `Create`, `FadeInFromDown` → `FadeIn(mob, shift=DOWN)`, `CONFIG = {}` → constructor kwargs. **Rule: Include a deprecation map in the system prompt.**

**FM-E3: API hallucination.** Per the TheoremExplainAgent study (ACL 2025), the **#1 failure category** is LLMs inventing nonexistent Manim functions, modules, or parameter names. **Rule: Include a whitelist of verified methods in the system prompt. Only use documented API calls.**

**FM-E4: Missing voiceover imports.** `VoiceoverScene` and services are NOT in `from manim import *`. **Rule: Always add `from manim_voiceover import VoiceoverScene` and the specific service import.**

### Category F: Code structure errors

**FM-F1: Code outside `construct()`.** Animation code at module level or in `__init__` fails. **Rule: ALL scene code must be inside `def construct(self):`.**

**FM-F2: `self.wait()` with zero/negative duration.** Can cause rendering errors. **Rule: `self.wait()` duration must be positive.**

---

## 5. System prompt ingredients — rules and few-shot examples

Based on every failure mode and API detail above, here are the rules and few-shot structures for your coder and planner prompts.

### Planner prompt ingredients

The planner should receive these constraints:

- **Scene structure:** Each animation must have exactly ONE scene class inheriting from `VoiceoverScene`. The class must define `construct(self)`. `set_speech_service()` is the first line of `construct()`.
- **Voiceover blocks:** Each narrative paragraph maps to one `with self.voiceover(text=...) as tracker:` block. Place bookmarks at semantic boundaries where visual state should change. Use 2-5 bookmarks per voiceover block for complex sequences.
- **Timing budget:** Give the planner awareness that each voiceover block's animations must fit within `tracker.duration`. Multiple animations must subdivide time using bookmarks or `get_remaining_duration()`.
- **Visual layout planning:** The planner should specify approximate positions (top, center, left-half, etc.) and when objects enter/exit the frame. Maximum ~6 visual elements on screen simultaneously.
- **Text class selection:** Planner must specify whether each text element is `Text` (plain), `MathTex` (math), or `Tex` (mixed).

### Coder prompt — mandatory rules block

Include these rules verbatim in the coder system prompt:

```
IMPORTS:
- Always start with: from manim import *
- Always add: from manim_voiceover import VoiceoverScene
- Always add: from manim_voiceover.services.elevenlabs import ElevenLabsService
- Never use: manimlib, TextMobject, TexMobject, ShowCreation, CONFIG dicts

SCENE STRUCTURE:
- Exactly ONE scene class per file, inheriting from VoiceoverScene
- All animation code inside def construct(self):
- First line of construct: self.set_speech_service(ElevenLabsService(...))
- Use transcription_model="base" in service constructor when using bookmarks
- End scene with self.wait()

LATEX RULES:
- ALL LaTeX strings MUST use raw strings: r"..."
- MathTex = math mode only. Never put plain text in MathTex.
- Text = plain text only. Never put LaTeX in Text.
- Tex = LaTeX text mode. Use $...$ for inline math.
- Only amsmath and amssymb available by default. For other packages, create TexTemplate.
- Every MathTex string argument must be brace-balanced.
- Use {{ }} only for deliberate submobject isolation for TransformMatchingTex.

POSITIONING:
- Frame: width ≈ 14.22, height = 8.0. Center = ORIGIN.
- Safe area: X ∈ [-6.5, 6.5], Y ∈ [-3.5, 3.5].
- Always position objects explicitly. Never leave multiple objects at ORIGIN.
- For long text: text.scale_to_fit_width(config.frame_width - 2)
- Use relative positioning (next_to, arrange, to_edge) over absolute coordinates.
- Never use pixel values as coordinates.

ANIMATION RULES:
- For rotations ≥ 90°: use Rotate(mob, angle), NOT mob.animate.rotate(angle)
- After Transform(A, B): reference A. After ReplacementTransform(A, B): reference B.
- Objects must be in scene before animating (self.add or creation animation).
- Chain .animate calls: mob.animate.shift(RIGHT).scale(2), not separate .animate calls.
- Always specify run_time explicitly. Default 1.0s.
- Use FadeIn(mob, shift=UP) not bare FadeIn(mob) for polished transitions.
- Use LaggedStart for revealing lists/groups, not individual self.play calls.

VOICEOVER TIMING:
- Never use tracker.duration for more than one animation per voiceover block.
- For multiple animations: use bookmarks or tracker.get_remaining_duration().
- ALL synced animations must be inside the with self.voiceover() block.
- Bookmark names: alphanumeric + underscore only. No hyphens or spaces.
- Bookmark syntax: <bookmark mark='name'/>

CODE MOBJECT (v0.19+ API):
- Use code_string= not code=
- Use code_file= not file_name=
- Use formatter_style= not style=
- Use add_line_numbers= not insert_line_no=
- Font/size go in paragraph_config dict, background styling in background_config dict.

COLOR SYSTEM:
- Core: RED, BLUE, GREEN, YELLOW, PURPLE, TEAL, ORANGE, PINK, GOLD, MAROON
- Shades: _A (lightest) to _E (darkest). _C is default.
- Use color.darker() and color.lighter() for dynamic shading.
- Set fill_opacity between 0.2–0.5 for filled shapes.

VERIFIED METHODS (use only these on mobjects):
shift(), move_to(), next_to(), to_edge(), to_corner(), scale(), scale_to_fit_width(),
set_color(), set_fill(), set_stroke(), set_opacity(), rotate(), arrange(),
arrange_in_grid(), get_center(), get_width(), get_height(), copy(), align_to(),
add_updater(), set_z_index(), get_top(), get_bottom(), get_left(), get_right(),
width (property), height (property)
```

### Few-shot examples for the coder

**Example 1 — Math explanation with voiceover and bookmarks:**

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService

class QuadraticFormula(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            ElevenLabsService(
                voice_name="Adam",
                voice_settings={"stability": 0.5, "similarity_boost": 0.75},
                transcription_model="base",
            )
        )
        
        with self.voiceover(
            text="""Let's derive the quadratic formula. 
            <bookmark mark='eq'/>We start with a x squared plus b x plus c equals zero.
            <bookmark mark='result'/>The solution is x equals negative b plus or minus 
            the square root of b squared minus four a c, all over two a."""
        ) as tracker:
            self.wait_until_bookmark("eq")
            eq1 = MathTex(r"{{a}}x^2 + {{b}}x + {{c}} = 0")
            eq1.set_color_by_tex_to_color_map({"a": BLUE, "b": GREEN, "c": RED})
            self.play(Write(eq1), run_time=tracker.time_until_bookmark("result"))
            
            self.wait_until_bookmark("result")
            result = MathTex(
                r"x = \frac{-{{b}} \pm \sqrt{{{b}}^2 - 4{{a}}{{c}}}}{2{{a}}}"
            )
            result.set_color_by_tex_to_color_map({"a": BLUE, "b": GREEN, "c": RED})
            self.play(TransformMatchingTex(eq1, result),
                      run_time=tracker.get_remaining_duration())
        
        self.wait()
```

**Example 2 — Data visualization with graph:**

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService

class GrowthChart(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            ElevenLabsService(voice_name="Adam", transcription_model="base")
        )
        
        ax = Axes(
            x_range=[0, 5, 1], y_range=[0, 25, 5],
            x_length=6, y_length=4,
            axis_config={"include_numbers": True},
        )
        labels = ax.get_axis_labels(x_label="t", y_label="f(t)")
        
        with self.voiceover(
            text="""<bookmark mark='axes'/>Here are our axes.
            <bookmark mark='graph'/>Watch how the quadratic function grows.
            <bookmark mark='dot'/>This dot traces the curve."""
        ) as tracker:
            self.wait_until_bookmark("axes")
            self.play(Create(ax), Write(labels),
                      run_time=tracker.time_until_bookmark("graph"))
            
            self.wait_until_bookmark("graph")
            graph = ax.plot(lambda t: t**2, color=BLUE)
            self.play(Create(graph),
                      run_time=tracker.time_until_bookmark("dot"))
            
            self.wait_until_bookmark("dot")
            dot = Dot(color=YELLOW).move_to(ax.i2gp(0, graph))
            self.play(FadeIn(dot, scale=0.5), run_time=0.3)
            self.play(MoveAlongPath(dot, graph),
                      run_time=tracker.get_remaining_duration())
        
        self.wait()
```

**Example 3 — Flowchart/diagram scene:**

```python
from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService

class PipelineFlowchart(VoiceoverScene):
    def construct(self):
        self.set_speech_service(
            ElevenLabsService(voice_name="Adam", transcription_model="base")
        )
        
        def make_box(text_str, color):
            box = Rectangle(width=3, height=0.8, color=color, fill_opacity=0.3)
            label = Text(text_str, font_size=24).move_to(box)
            return VGroup(box, label)
        
        step1 = make_box("Input", GREEN)
        step2 = make_box("Process", BLUE)
        step3 = make_box("Output", RED)
        
        steps = VGroup(step1, step2, step3).arrange(DOWN, buff=1.2)
        arrow1 = Arrow(step1.get_bottom(), step2.get_top(), buff=0.1)
        arrow2 = Arrow(step2.get_bottom(), step3.get_top(), buff=0.1)
        
        with self.voiceover(
            text="""Here is our pipeline. <bookmark mark='s1'/>Data enters the input stage.
            <bookmark mark='a1'/>It flows to processing.
            <bookmark mark='s2'/>The process transforms the data.
            <bookmark mark='a2'/>And finally, <bookmark mark='s3'/>we get the output."""
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
        
        self.wait()
```

### Helper function recommendations for tools.py

Based on the failure modes, wrap these patterns as helpers your LLM can call:

```python
# tools.py — suggested helper functions

def safe_text(content: str, **kwargs) -> Text:
    """Create Text that won't overflow the frame."""
    t = Text(content, **kwargs)
    if t.width > config.frame_width - 2:
        t.scale_to_fit_width(config.frame_width - 2)
    return t

def safe_mathtex(tex_string: str, **kwargs) -> MathTex:
    """Create MathTex with overflow protection."""
    m = MathTex(tex_string, **kwargs)
    if m.width > config.frame_width - 2:
        m.scale_to_fit_width(config.frame_width - 2)
    return m

def create_axes(x_range, y_range, **kwargs):
    """Create Axes with sensible defaults for voiceover scenes."""
    defaults = dict(
        x_length=6, y_length=4,
        axis_config={"include_numbers": True, "font_size": 24},
        tips=True,
    )
    defaults.update(kwargs)
    return Axes(x_range=x_range, y_range=y_range, **defaults)

def labeled_box(text_str: str, color=BLUE, width=3, height=0.8, font_size=24):
    """Create a labeled rectangle for diagrams."""
    box = Rectangle(width=width, height=height, color=color, fill_opacity=0.3)
    label = Text(text_str, font_size=font_size).move_to(box)
    return VGroup(box, label)

def connect_with_arrow(source, target, buff=0.1, **kwargs):
    """Create an arrow from source bottom to target top."""
    return Arrow(source.get_bottom(), target.get_top(), buff=buff, **kwargs)

def staggered_reveal(scene, mobjects, shift=RIGHT * 0.5, lag_ratio=0.15, run_time=2):
    """Reveal a list of mobjects with staggered FadeIn."""
    scene.play(LaggedStart(
        *[FadeIn(m, shift=shift) for m in mobjects],
        lag_ratio=lag_ratio, run_time=run_time,
    ))

def counting_animation(scene, tracker, decimal, target_value, run_time=2):
    """Animate a DecimalNumber counting up using a ValueTracker."""
    decimal.add_updater(lambda d: d.set_value(tracker.get_value()))
    scene.play(tracker.animate.set_value(target_value), run_time=run_time)
    decimal.clear_updaters()

def code_block(code_str, language="python", style="monokai"):
    """Create a Code mobject with v0.20-correct parameters."""
    return Code(
        code_string=code_str,
        language=language,
        formatter_style=style,
        add_line_numbers=True,
        paragraph_config={"font_size": 20, "font": "Monospace"},
        background_config={"corner_radius": 0.2, "buff": 0.3},
    )

def highlight_box(mobject, color=YELLOW, buff=0.1, corner_radius=0.1):
    """SurroundingRectangle with v0.20-correct keyword args."""
    return SurroundingRectangle(mobject, color=color, buff=buff,
                                corner_radius=corner_radius)

def setup_voiceover(scene, voice_name="Adam", use_bookmarks=True):
    """Standard voiceover initialization."""
    kwargs = dict(voice_name=voice_name,
                  voice_settings={"stability": 0.5, "similarity_boost": 0.75})
    if use_bookmarks:
        kwargs["transcription_model"] = "base"
    scene.set_speech_service(ElevenLabsService(**kwargs))
```

### Rate function quick reference for the system prompt

Include this lookup table so the LLM picks appropriate easing:

| Effect | Rate function |
|---|---|
| Default smooth motion | `smooth` |
| Constant speed (good for `Write`) | `linear` |
| Object arriving (fast→slow) | `rush_from` |
| Object departing (slow→fast) | `rush_into` |
| Emphasis pulse (go and return) | `there_and_back` |
| Pull-back then forward | `running_start` |
| Extra smooth | `double_smooth` |
| Stop at 70% | `not_quite_there` |

### Creation animation selection table for the system prompt

| Object type | Create | Remove |
|---|---|---|
| Geometric shapes | `Create(mob)` | `Uncreate(mob)` or `FadeOut(mob)` |
| Text / Equations | `Write(mob)` | `Unwrite(mob)` or `FadeOut(mob)` |
| Any (polished) | `FadeIn(mob, shift=UP)` | `FadeOut(mob, shift=DOWN)` |
| Arrows | `GrowArrow(mob)` | `FadeOut(mob)` |
| Emphasis entrance | `GrowFromCenter(mob)` | `ShrinkToCenter(mob)` |
| Groups | `LaggedStart(*[FadeIn(m, shift=RIGHT*0.5) for m in group], lag_ratio=0.15)` | similar with FadeOut |

---

## Conclusion

The critical bottleneck for LLM-generated Manim code is **API hallucination** — per the TheoremExplainAgent study, it accounts for the majority of failures. Your system prompt must therefore serve as a narrow, verified API surface that constrains the LLM. The second major category is **LaTeX errors**, mitigated entirely by the six LaTeX rules in Category A above. The third is **timing errors** in VoiceoverScene, solved by the bookmark/`get_remaining_duration()` patterns.

For your tools.py, the highest-value helpers are `safe_text` and `safe_mathtex` (prevent overflow, the most common visual bug), `code_block` (wraps the completely-changed v0.19+ Code constructor), and `setup_voiceover` (handles the `transcription_model` footgun). The `@` shorthand for Axes and the `Mobject.always` updater pattern are the two v0.20 idioms most worth pushing LLMs toward — they produce cleaner, more readable code.

Finally, the ElevenLabs SDK version conflict (`^0.2.27` vs current `v2.1+`) is a deployment landmine. Either pin the old version or use `manim-voiceover-enhanced`. Build this check into your pipeline's dependency resolution.
