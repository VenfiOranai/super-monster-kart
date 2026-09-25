"""M0 Mode 7 spike: a free camera over the calibration texture (GDD §17).

Run: python -m tools.mode7_spike [--vsync]

  --vsync      lock presentation to the display refresh

Controls
  Up / Down        move forward / back
  Left / Right     turn
  A / D            strafe
  R / F            raise / lower the camera
  T / G            move the horizon up / down
  Space            toggle auto-orbit (hands-free benchmarking)
  1 2 3 4 5        window 720p / 1080p / 1440p / 4K / awkward 1000x700
  Esc              quit

Timings are printed once a second and shown in the title bar. Without
--vsync the loop is uncapped, so fps shows the real headroom.
"""

import argparse
import dataclasses
import math
import time

import pygame

from smk import reporting
from smk.app.bootstrap import setup
from smk.render.mode7 import Mode7Camera, Mode7Plane, Mode7Renderer
from smk.render.screen import Screen, Viewport
from tools.calibration import CalibrationTexture
from tools.performance import PerformanceReporter, StageStats


class Mode7Spike:
    TITLE = "SMK Mode 7 spike"
    BUDGET_MS = 1000 / 144 * 0.6  # 144 fps with 40% spare (GDD §17)
    REPORT_INTERVAL = 1.0
    MAX_FRAME_DT = 0.1
    SKY_COLOUR = (96, 144, 216)

    MOVE_SPEED = 200.0  # texels per second
    TURN_SPEED = 1.8  # radians per second
    CLIMB_SPEED = 60.0
    HORIZON_SPEED = 40.0  # rows per second
    MIN_HEIGHT, MAX_HEIGHT = 2.0, 400.0
    MIN_HORIZON, MAX_HORIZON = 0, Screen.INTERNAL_SIZE[1] - 10

    WINDOW_PRESETS = {
        pygame.K_1: (1280, 720),
        pygame.K_2: (1920, 1080),
        pygame.K_3: (2560, 1440),
        pygame.K_4: (3840, 2160),
        pygame.K_5: (1000, 700),
    }

    def __init__(self, vsync: bool) -> None:
        self._performance = PerformanceReporter()
        reporting.install(self._performance)
        self._screen = Screen(self.TITLE, vsync=vsync)
        self._vsync = vsync
        texture = pygame.surfarray.map_array(self._screen.buffer, CalibrationTexture.generate())
        self._renderer = Mode7Renderer(Mode7Plane(texture), Screen.INTERNAL_SIZE)
        self._camera = Mode7Camera(x=512.0, y=900.0, angle=-math.pi / 2)
        self._horizon = float(self._camera.horizon_y)
        self._orbiting = False
        self._orbit_time = 0.0
        self._running = False

    def run(self) -> None:
        self._running = True
        last = time.perf_counter()
        next_report = last + self.REPORT_INTERVAL
        try:
            while self._running:
                now = time.perf_counter()
                dt = min(now - last, self.MAX_FRAME_DT)
                last = now
                self._handle_events()
                self._update_camera(dt)
                self._draw()
                reporting.reporter.end_frame()
                if now >= next_report:
                    self._report()
                    next_report = now + self.REPORT_INTERVAL
        finally:
            pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._running = False
                elif event.key == pygame.K_SPACE:
                    self._orbiting = not self._orbiting
                elif event.key in self.WINDOW_PRESETS:
                    self._screen.window.size = self.WINDOW_PRESETS[event.key]
                    self._performance.reset()

    def _update_camera(self, dt: float) -> None:
        camera = self._camera
        if self._orbiting:
            self._orbit_time += dt
            t = self._orbit_time / 4
            camera = dataclasses.replace(
                camera, x=512 + 300 * math.cos(t), y=512 + 300 * math.sin(t), angle=t * 3
            )
        else:
            keys = pygame.key.get_pressed()
            turn = keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]
            advance = keys[pygame.K_UP] - keys[pygame.K_DOWN]
            strafe = keys[pygame.K_d] - keys[pygame.K_a]
            angle = camera.angle + turn * self.TURN_SPEED * dt
            camera = dataclasses.replace(camera, angle=angle)
            (fx, fy), (rx, ry) = camera.forward, camera.right
            step = self.MOVE_SPEED * dt
            camera = dataclasses.replace(
                camera,
                x=camera.x + (fx * advance + rx * strafe) * step,
                y=camera.y + (fy * advance + ry * strafe) * step,
            )

        keys = pygame.key.get_pressed()
        climb = keys[pygame.K_r] - keys[pygame.K_f]
        height = min(max(camera.height + climb * self.CLIMB_SPEED * dt, self.MIN_HEIGHT), self.MAX_HEIGHT)
        raise_horizon = keys[pygame.K_t] - keys[pygame.K_g]
        self._horizon = min(
            max(self._horizon - raise_horizon * self.HORIZON_SPEED * dt, self.MIN_HORIZON), self.MAX_HORIZON
        )
        self._camera = dataclasses.replace(camera, height=height, horizon_y=round(self._horizon))

    def _draw(self) -> None:
        buffer = self._screen.buffer
        with reporting.reporter.measure("mode7"):
            buffer.fill(self.SKY_COLOUR, pygame.Rect(0, 0, buffer.get_width(), self._camera.horizon_y))
            pixels = pygame.surfarray.pixels2d(buffer)
            self._renderer.render(self._camera, pixels)
            del pixels  # unlocks the surface
        self._screen.render()

    def _report(self) -> None:
        performance = self._performance
        stats = performance.stats()
        if "frame" not in stats:
            return
        fps = performance.frame_count / (sum(performance.samples("frame")) / 1000)
        window_size = self._screen.window.size
        scale = Viewport.fit(Screen.INTERNAL_SIZE, window_size).scale
        work = self._work()
        verdict = "OK" if work.p99_ms <= self.BUDGET_MS else "OVER"
        stages = " | ".join(f"{name} {s.mean_ms:.2f}" for name, s in stats.items() if name != "frame")
        line = (
            f"{'vsync' if self._vsync else 'uncapped'} {window_size[0]}x{window_size[1]} @{scale}x | "
            f"{fps:.0f} fps | frame {stats['frame'].mean_ms:.2f} ms | {stages} | "
            f"work p99 {work.p99_ms:.2f} of {self.BUDGET_MS:.2f} {verdict}"
        )
        print(line, flush=True)
        self._screen.window.title = f"{self.TITLE} | {line}"
        performance.reset()

    def _work(self) -> StageStats:
        """Time spent drawing and presenting, as the sum of the measured stages.

        Whole-frame time is not used: uncapped at thousands of fps, its tail
        is dominated by OS scheduling noise and this report's own printing.
        With vsync the flip is mostly waiting for the display, which is not
        cost, so it is left out.
        """
        return self._performance.total(excluding=("flip",) if self._vsync else ())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--vsync", action="store_true", help="lock presentation to the display refresh")
    args = parser.parse_args()
    setup()
    Mode7Spike(vsync=args.vsync).run()


if __name__ == "__main__":
    main()
