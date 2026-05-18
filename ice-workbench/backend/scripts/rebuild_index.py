"""Rebuild SQLite cache index from filesystem source of truth."""
from __future__ import annotations

import asyncio

from app.seed.runner import bootstrap


def main() -> None:
    asyncio.run(bootstrap())
    print("rebuild_index: ok")


if __name__ == "__main__":
    main()
