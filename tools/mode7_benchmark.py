"""M0 benchmark: Mode 7 plus presentation cost at each output size (GDD §17).

Run: python -m tools.mode7_benchmark [--frames N]

Opens a real window and resizes it through each output size, drawing the
plane and presenting it with vsync off, then checks the whole frame against
the M0 exit budget: 144 fps with 40% of the frame spare. Exits non-zero if
any size is over budget.
"""

import argparse
import math
import sys

import pygame

from smk import reporting
from smk.app.bootstrap import setup
from smk.render.mode7 import Mode7Camera, Mode7Plane, Mode7Renderer
from smk.render.screen import Screen
from tools.calibration import CalibrationTexture
from tools.performance import PerformanceReporter


class Mode7Benchmark:
    TARGET_FPS = 144
    REQUIRED_SPARE = 0.40
    OUTPUTS = {
        "720p": (1280, 720),
        "1080p": (1920, 1080),
        "1440p": (2560, 1440),
        "4K": (3840, 2160),
        "awkward": (1000, 700),
    }
    WARMUP_FRAMES = 60

    def __init__(self, frames: int) -> None:
        self._frames = frames
        self._budget_ms = 1000 / self.TARGET_FPS * (1 - self.REQUIRED_SPARE)

    def run(self) -> bool:
        try:
            performance = PerformanceReporter()
            reporting.install(performance)
            screen = Screen("mode7 benchmark", vsync=False)
            texture = pygame.surfarray.map_array(screen.buffer, CalibrationTexture.generate())
            renderer = Mode7Renderer(Mode7Plane(texture), Screen.INTERNAL_SIZE)
            print(f"Video driver: {pygame.display.get_driver()}")
            print(f"Budget: {self._budget_ms:.2f} ms/frame "
                  f"({self.TARGET_FPS} fps with {self.REQUIRED_SPARE:.0%} spare), "
                  f"{self._frames} frames per size\n")
            return all([self._measure(name, size, screen, renderer, performance) for name, size in self.OUTPUTS.items()])
        finally:
            pygame.quit()

    def _measure(self, name, size, screen, renderer, performance) -> bool:
        screen.window.size = size
        for frame in range(self.WARMUP_FRAMES + self._frames):
            if frame == self.WARMUP_FRAMES:
                performance.reset()
            pygame.event.pump()
            with reporting.reporter.measure("mode7"):
                pixels = pygame.surfarray.pixels2d(screen.buffer)
                renderer.render(self._camera(frame), pixels)
                del pixels  # unlocks the surface
            screen.render()
            reporting.reporter.end_frame()

        stats = performance.stats()
        stages = [name for name in stats if name != "frame"]
        total = performance.total()
        ok = total.p99_ms <= self._budget_ms
        actual = screen.window.size
        breakdown = "  ".join(f"{s} {stats[s].mean_ms:.3f}" for s in stages)
        print(f"{name:<8} {actual[0]:>5}x{actual[1]:<5} total {total.mean_ms:6.3f} ms  p99 {total.p99_ms:6.3f} ms"
              f"  {'PASS' if ok else 'FAIL'}   ({breakdown})")
        if actual != size:
            print(f"         (requested {size[0]}x{size[1]}; the window is {actual[0]}x{actual[1]})")
        return ok

    def _camera(self, frame: int) -> Mode7Camera:
        # Orbit the texture while turning, so every rotation and memory-access pattern is exercised.
        t = frame / 240
        return Mode7Camera(x=512 + 300 * math.cos(t), y=512 + 300 * math.sin(t), angle=t * 3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--frames", type=int, default=1200, help="measured frames per output size")
    args = parser.parse_args()
    setup()
    sys.exit(0 if Mode7Benchmark(args.frames).run() else 1)
