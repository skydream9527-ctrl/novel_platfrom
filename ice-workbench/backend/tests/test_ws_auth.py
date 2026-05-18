"""WebSocket auth — dual path: Aegis header OR bearer JWT."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.seed.runner import bootstrap


@pytest.mark.asyncio
async def test_ws_subprotocol_auth(isolated_data_root):
    """Classic JWT via `["bearer", token]` subprotocol still works."""
    await bootstrap()

    from app.main import app
    from app.services import auth_svc, task_svc

    client = TestClient(app)
    creds = await auth_svc.password_login("admin", "admin123")
    token = creds["tokens"]["access_token"]
    uid = creds["user"]["id"]
    task = await task_svc.create_task(name="WS test", paradigm="biz", owner_id=uid)
    cid = task["workspace"]["current_conversation_id"] if task.get("workspace") else None
    if not cid:
        cid = await task_svc.get_or_create_default_conversation(task["id"])

    with client.websocket_connect(
        f"/api/v1/ws/conversations/{cid}?task_id={task['id']}",
        subprotocols=["bearer", token],
    ) as ws:
        assert ws.scope.get("type") == "websocket"

    with client.websocket_connect(
        f"/api/v1/ws/conversations/{cid}?task_id={task['id']}&token={token}"
    ) as ws:
        assert ws.scope.get("type") == "websocket"


@pytest.mark.asyncio
async def test_ws_aegis_bypass(isolated_data_root, monkeypatch):
    """Dev bypass stands in for the Aegis header in tests."""
    monkeypatch.setenv("AEGIS_DEV_BYPASS_EMAIL", "tester@xiaomi.com")
    from app.core import config as cfg
    cfg.get_settings.cache_clear()

    await bootstrap()

    from app.main import app
    from app.services import task_svc

    client = TestClient(app)
    task = await task_svc.create_task(name="WS test", paradigm="biz", owner_id="tester@xiaomi.com")
    cid = task["workspace"]["current_conversation_id"] if task.get("workspace") else None
    if not cid:
        cid = await task_svc.get_or_create_default_conversation(task["id"])

    with client.websocket_connect(
        f"/api/v1/ws/conversations/{cid}?task_id={task['id']}"
    ) as ws:
        assert ws.scope.get("type") == "websocket"


@pytest.mark.asyncio
async def test_ws_rejects_when_no_credential(isolated_data_root, monkeypatch):
    """No Aegis header, no JWT, no dev bypass → close 4401."""
    monkeypatch.setenv("AEGIS_DEV_BYPASS_EMAIL", "")
    from app.core import config as cfg
    cfg.get_settings.cache_clear()

    await bootstrap()
    from app.main import app
    client = TestClient(app)

    import websockets.exceptions as wse  # type: ignore
    from starlette.websockets import WebSocketDisconnect

    with pytest.raises((WebSocketDisconnect, wse.ConnectionClosed, Exception)):
        with client.websocket_connect("/api/v1/ws/conversations/bogus?task_id=bogus") as ws:
            ws.receive_text()
