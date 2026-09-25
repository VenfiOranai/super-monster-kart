"""Entry point: `python -m smk` or the `smk` console script."""

from smk.app.bootstrap import setup
from smk.app.game import Game


def main() -> None:
    setup()
    Game().run()


if __name__ == "__main__":
    main()
