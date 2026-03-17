"""12 helper utilities for robust Manim + voiceover scene generation."""

from typing import Optional

from manim import *
from manim_voiceover import VoiceoverScene
from manim_voiceover.services.elevenlabs import ElevenLabsService


# Text helpers

def safe_text(content: str, **kwargs) -> Text:
    """Create Text constrained to the frame width."""
    t = Text(content, **kwargs)
    if t.width > config.frame_width - 2:
        t.scale_to_fit_width(config.frame_width - 2)
    return t


def safe_mathtex(tex_string: str, **kwargs) -> MathTex:
    """Create MathTex constrained to the frame width."""
    m = MathTex(tex_string, **kwargs)
    if m.width > config.frame_width - 2:
        m.scale_to_fit_width(config.frame_width - 2)
    return m


def show_title(text: str, subtitle: Optional[str] = None) -> VGroup:
    """Create centered title with optional subtitle."""
    title = safe_text(text, font_size=48, color=WHITE)
    group = VGroup(title)
    if subtitle:
        sub = safe_text(subtitle, font_size=28, color=GRAY_B)
        sub.next_to(title, DOWN, buff=0.4)
        group.add(sub)
    group.move_to(ORIGIN)
    return group


# Axes and plotting

def create_axes(
    x_range: tuple = (-4, 4, 1),
    y_range: tuple = (-3, 3, 1),
    x_label: str = "x",
    y_label: str = "y",
    x_length: float = 6,
    y_length: float = 4,
) -> VGroup:
    """Create labeled axes using API compatible with Manim 0.20/0.19."""
    axes = Axes(
        x_range=x_range,
        y_range=y_range,
        x_length=x_length,
        y_length=y_length,
        axis_config={"include_numbers": True, "font_size": 24},
        tips=True,
    )
    labels = axes.get_axis_labels(Text(x_label, font_size=24), Text(y_label, font_size=24))
    return VGroup(axes, labels)


def plot_function(axes: Axes, func, color=BLUE, x_range=None):
    """Plot a function over a reasonable default range."""
    plot_range = x_range or [axes.x_range[0] + 0.5, axes.x_range[1] - 0.5]
    return axes.plot(func, x_range=plot_range, color=color, stroke_width=3)


def animate_dot_along_curve(
    scene,
    axes: Axes,
    func,
    x_start: float,
    x_end: float,
    duration: float = 3.0,
    color=YELLOW,
):
    """Animate a dot moving along plotted curve path."""
    dot = Dot(axes.c2p(x_start, func(x_start)), color=color, radius=0.12)
    scene.play(FadeIn(dot, scale=2), run_time=0.3)
    curve_path = axes.plot(func, x_range=[x_start, x_end])
    scene.play(MoveAlongPath(dot, curve_path), run_time=duration - 0.3, rate_func=smooth)
    return dot


# Diagram helpers

def labeled_box(
    text_str: str,
    color=BLUE,
    width: float = 3,
    height: float = 0.8,
    font_size: int = 24,
    fill_opacity: float = 0.3,
) -> VGroup:
    """Create a labeled diagram box."""
    box = Rectangle(
        width=width,
        height=height,
        color=color,
        fill_opacity=fill_opacity,
        fill_color=color,
    )
    label = Text(text_str, font_size=font_size).move_to(box)
    return VGroup(box, label)


def connect_with_arrow(source, target, buff: float = 0.1, color=WHITE, label: Optional[str] = None) -> VGroup:
    """Connect source->target with optional arrow label."""
    arrow = Arrow(source.get_bottom(), target.get_top(), buff=buff, color=color, stroke_width=3)
    group = VGroup(arrow)
    if label:
        lbl = Text(label, font_size=20, color=color)
        lbl.next_to(arrow, RIGHT, buff=0.1)
        group.add(lbl)
    return group


def highlight_box(mobject, color=YELLOW, buff: float = 0.1, corner_radius: float = 0.1):
    """Create SurroundingRectangle with keyword-only style for compatibility."""
    return SurroundingRectangle(mobject, color=color, buff=buff, corner_radius=corner_radius)


def staggered_reveal(scene, mobjects, shift=RIGHT * 0.5, lag_ratio: float = 0.15, run_time: float = 2.0):
    """Reveal objects with lagged fade-ins."""
    scene.play(
        LaggedStart(*[FadeIn(m, shift=shift) for m in mobjects], lag_ratio=lag_ratio, run_time=run_time)
    )


# Code display helper

def code_block(code_str: str, language: str = "python", style: str = "monokai"):
    """Create a Code mobject using v0.19+ argument names."""
    return Code(
        code_string=code_str,
        language=language,
        formatter_style=style,
        add_line_numbers=True,
        paragraph_config={"font_size": 20, "font": "Monospace"},
        background_config={"corner_radius": 0.2, "buff": 0.3, "fill_opacity": 1},
    )


# Voiceover setup

def setup_voiceover(scene: VoiceoverScene, voice_name: str = "Adam", use_bookmarks: bool = True):
    """Initialize ElevenLabs voice service for a VoiceoverScene."""
    kwargs = {
        "voice_name": voice_name,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    if use_bookmarks:
        kwargs["transcription_model"] = "base"
    else:
        # Explicitly disable transcription to avoid whisper dependency prompts.
        kwargs["transcription_model"] = None
    print(
        "[setup_voiceover] provider=elevenlabs "
        f"use_bookmarks={use_bookmarks} transcription_model={kwargs['transcription_model']}"
    )
    scene.set_speech_service(ElevenLabsService(**kwargs))


# Scene utility

def fade_out_all(scene, duration: float = 0.5):
    """Fade out all current mobjects if present."""
    if scene.mobjects:
        scene.play(*[FadeOut(m) for m in scene.mobjects[:]], run_time=duration)
