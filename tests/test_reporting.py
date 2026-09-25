from smk import reporting
from smk.reporting import Reporter


class CountingReporter(Reporter):
    def __init__(self) -> None:
        self.frames = 0

    def end_frame(self) -> None:
        self.frames += 1


def test_default_reporter_accepts_every_hook_silently():
    with Reporter().measure("anything"):
        pass
    Reporter().end_frame()


def test_install_swaps_the_global_and_returns_the_previous_one():
    counting = CountingReporter()
    previous = reporting.install(counting)
    try:
        reporting.reporter.end_frame()
        with reporting.reporter.measure("inherited no-op"):
            pass
        assert counting.frames == 1
    finally:
        reporting.install(previous)
    assert reporting.reporter is previous
