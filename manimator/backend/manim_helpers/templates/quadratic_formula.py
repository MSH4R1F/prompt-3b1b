from manim import *
from manim_voiceover import VoiceoverScene

from manim_helpers.tools import fade_out_all, safe_mathtex, setup_voiceover


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
