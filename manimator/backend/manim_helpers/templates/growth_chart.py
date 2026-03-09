from manim import *
from manim_voiceover import VoiceoverScene

from manim_helpers.tools import create_axes, fade_out_all, setup_voiceover


class GrowthChart(VoiceoverScene):
    def construct(self):
        setup_voiceover(self)

        ax_group = create_axes(x_range=[0, 5, 1], y_range=[0, 25, 5], x_label="t", y_label="f(t)")
        ax = ax_group[0]

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
            dot = Dot(color=YELLOW).move_to(ax.c2p(0, 0))
            self.play(FadeIn(dot, scale=0.5), run_time=0.3)
            self.play(MoveAlongPath(dot, graph), run_time=tracker.get_remaining_duration())

        fade_out_all(self)
        self.wait(0.5)
