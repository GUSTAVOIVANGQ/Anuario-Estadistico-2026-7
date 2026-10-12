"""Figura H.13: radio en Guadalajara, ODS manual."""
from pathlib import Path
import sys

FIGURE_ID = 'H.13'


def generate(context):
    from anuario2026.inram_radio import generate_radio
    return generate_radio(context)


def main():
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'src'))
    from anuario2026.cli import main as cli_main
    return cli_main(['run', '--only', FIGURE_ID])


if __name__ == '__main__':
    raise SystemExit(main())
