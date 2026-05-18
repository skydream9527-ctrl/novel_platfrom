"""Advisory file lock helpers (portalocker)."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import time

import portalocker


@contextmanager
def file_lock(path: Path, timeout: float = 5.0) -> Iterator[None]:
    """Acquire an exclusive advisory lock on `path`.lock.

    Lock file lives next to the target. Cross-process safe via flock.
    """
    lock_path = path.with_suffix(path.suffix + ".lock") if path.suffix else path.with_name(path.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(lock_path, "a+")
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                portalocker.lock(fh, portalocker.LOCK_EX | portalocker.LOCK_NB)
                break
            except portalocker.LockException:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)
        yield
    finally:
        try:
            portalocker.unlock(fh)
        finally:
            fh.close()


@contextmanager
def multi_lock(paths: list[Path], timeout: float = 5.0) -> Iterator[None]:
    """Lock several files in dictionary order to avoid deadlocks (D139)."""
    sorted_paths = sorted(set(paths), key=lambda p: str(p))
    locks = []
    try:
        for p in sorted_paths:
            cm = file_lock(p, timeout=timeout)
            cm.__enter__()
            locks.append(cm)
        yield
    finally:
        for cm in reversed(locks):
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass
