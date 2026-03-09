"""Render-oriented tests for every helper in tools.py."""

from manim import Axes, Circle, Code, DOWN, SurroundingRectangle, VGroup, config

from manim_helpers.tools import (
    code_block,
    connect_with_arrow,
    create_axes,
    highlight_box,
    labeled_box,
    plot_function,
    safe_mathtex,
    safe_text,
    show_title,
)


def test_safe_text_short():
    mob = safe_text("Hello World")
    assert mob.width <= config.frame_width - 2


def test_safe_text_long():
    mob = safe_text("A" * 200, font_size=48)
    assert mob.width <= config.frame_width - 2


def test_safe_mathtex():
    mob = safe_mathtex(r"\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}")
    assert mob.width <= config.frame_width - 2


def test_show_title_no_subtitle():
    group = show_title("Gradient Descent")
    assert isinstance(group, VGroup)
    assert len(group) == 1


def test_show_title_with_subtitle():
    group = show_title("Gradient Descent", subtitle="A visual introduction")
    assert isinstance(group, VGroup)
    assert len(group) == 2


def test_create_axes_returns_vgroup():
    result = create_axes()
    assert isinstance(result, VGroup)
    assert isinstance(result[0], Axes)


def test_plot_function():
    axes_group = create_axes()
    axes = axes_group[0]
    curve = plot_function(axes, lambda x: x**2)
    assert curve is not None


def test_labeled_box():
    from manim import GREEN

    box = labeled_box("Input", color=GREEN)
    assert isinstance(box, VGroup)
    assert len(box) == 2


def test_connect_with_arrow_no_label():
    b1 = labeled_box("A")
    b2 = labeled_box("B")
    b2.shift(3 * DOWN)
    arrow = connect_with_arrow(b1, b2)
    assert isinstance(arrow, VGroup)


def test_connect_with_arrow_with_label():
    b1 = labeled_box("A")
    b2 = labeled_box("B")
    b2.shift(3 * DOWN)
    arrow = connect_with_arrow(b1, b2, label="flow")
    assert isinstance(arrow, VGroup)
    assert len(arrow) == 2


def test_highlight_box():
    mob = Circle()
    rect = highlight_box(mob)
    assert isinstance(rect, SurroundingRectangle)


def test_code_block():
    mob = code_block("print('hello')", language="python")
    assert isinstance(mob, Code)
