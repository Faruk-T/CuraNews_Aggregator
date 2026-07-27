"""CLI entrypoint: ``python -m curanews``."""

from __future__ import annotations

from curanews import __version__


def main() -> None:
    print("CuraNews Aggregator — skeleton OK (day 1)")
    print(f"package: curanews v{__version__}")


if __name__ == "__main__":
    main()
