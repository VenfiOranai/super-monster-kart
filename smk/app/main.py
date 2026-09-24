"""Entry point: `python -m smk` or the `smk` console script."""

from smk.app.game import Game


def main() -> None:
    Game().run()


if __name__ == "__main__":
    main()
