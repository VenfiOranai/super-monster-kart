"""Hooks game code calls to report what it is doing, and the one global reporter.

The base ``Reporter`` does nothing, so reporting costs the game nothing
unless a dev tool installs a subclass that listens (see ``tools/``). Always
reach the reporter through the module — ``reporting.reporter.measure(...)`` —
because ``from smk.reporting import reporter`` would keep hold of whichever
instance was installed at import time.
"""

from collections.abc import Iterator
from contextlib import contextmanager


class Reporter:
    """The silent default. Subclasses override the hooks they care about."""

    # Performance

    @contextmanager
    def measure(self, name: str) -> Iterator[None]:
        """Wraps one named stage of the current frame."""
        yield

    def end_frame(self) -> None:
        """Marks the end of a rendered frame."""


reporter: Reporter = Reporter()


def install(new_reporter: Reporter) -> Reporter:
    """Replace the global reporter; returns the one it replaced."""
    global reporter
    previous, reporter = reporter, new_reporter
    return previous
