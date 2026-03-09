from manim import BLUE, Circle, Create, Scene


class SmokeTest(Scene):
    def construct(self):
        circle = Circle(color=BLUE)
        self.play(Create(circle))
        self.wait(0.5)
