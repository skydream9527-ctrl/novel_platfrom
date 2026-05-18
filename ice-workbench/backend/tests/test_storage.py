from __future__ import annotations

from pathlib import Path

import pytest

from app.core.storage import file_transaction, get_paths, read_json


def test_file_transaction_commit(isolated_data_root):
    p = get_paths()
    target = p.tasks / "task-1" / "meta.json"
    with file_transaction([target]) as tx:
        tx.makedirs([target.parent])
        tx.write_json(target, {"id": "task-1", "name": "demo"})
    assert read_json(target)["name"] == "demo"


def test_file_transaction_rollback(isolated_data_root):
    p = get_paths()
    a = p.tasks / "x" / "meta.json"
    b = p.users / "u1" / "tasks" / "index.json"
    a.parent.mkdir(parents=True, exist_ok=True)
    a.write_text('{"id":"x","name":"orig"}', encoding="utf-8")

    with pytest.raises(RuntimeError):
        with file_transaction([a, b]) as tx:
            tx.write_json(a, {"id": "x", "name": "changed"})
            raise RuntimeError("boom")

    assert read_json(a)["name"] == "orig"
    assert not b.exists()
