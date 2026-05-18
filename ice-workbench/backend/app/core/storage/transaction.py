"""file_transaction context — multi-file write with rollback semantics."""
from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .jsonio import read_json, write_json
from .lock import multi_lock


class FileTransaction:
    def __init__(self, paths: list[Path]):
        self._target_paths = [Path(p) for p in paths]
        self._backups: dict[Path, Path] = {}
        self._writes: dict[Path, Any] = {}
        self._dir_creates: list[Path] = []
        self._committed = False

    def read_json(self, path: Path | str, default: Any = None) -> Any:
        if path in self._writes:
            return self._writes[Path(path)]
        return read_json(path, default)

    def write_json(self, path: Path | str, data: Any) -> None:
        self._writes[Path(path)] = data

    def makedirs(self, paths: list[Path] | list[str]) -> None:
        for p in paths:
            self._dir_creates.append(Path(p))

    def _backup(self, p: Path) -> None:
        if not p.exists():
            return
        fd, name = tempfile.mkstemp(prefix=".bak-", dir=str(p.parent))
        import os

        os.close(fd)
        shutil.copy2(p, name)
        self._backups[p] = Path(name)

    def commit(self) -> None:
        for p in self._dir_creates:
            p.mkdir(parents=True, exist_ok=True)
        for p, data in self._writes.items():
            self._backup(p)
            write_json(p, data)
        for bak in self._backups.values():
            try:
                bak.unlink()
            except OSError:
                pass
        self._committed = True

    def rollback(self) -> None:
        for p, bak in self._backups.items():
            try:
                shutil.copy2(bak, p)
            except OSError:
                pass
            try:
                bak.unlink()
            except OSError:
                pass


@contextmanager
def file_transaction(paths: list[Path] | list[str]) -> Iterator[FileTransaction]:
    p_list = [Path(p) for p in paths]
    tx = FileTransaction(p_list)
    with multi_lock(p_list):
        try:
            yield tx
            tx.commit()
        except Exception:
            tx.rollback()
            raise
