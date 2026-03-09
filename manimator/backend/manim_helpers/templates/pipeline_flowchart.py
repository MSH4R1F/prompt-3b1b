from manim import *
from manim_voiceover import VoiceoverScene

from manim_helpers.tools import connect_with_arrow, fade_out_all, labeled_box, setup_voiceover


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
            self.play(FadeIn(step3, shift=DOWN), run_time=tracker.get_remaining_duration())

        fade_out_all(self)
        self.wait(0.5)
