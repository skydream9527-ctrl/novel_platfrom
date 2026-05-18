"""HTTP endpoint tests for the dual-auth chain (米盾 OR JWT)."""
from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi.testclient import TestClient

from app.seed.runner import bootstrap


def _sign_aegis(payload: dict, priv: rsa.RSAPrivateKey) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()
    sig = priv.sign(data, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(data).decode() + "." + base64.b64encode(sig).decode()


def _pub_b64(pk: rsa.RSAPublicKey) -> str:
    der = pk.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(der).decode()


@pytest.fixture
def aegis_keypair(monkeypatch):
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setenv("AEGIS_PUBLIC_KEY", _pub_b64(priv.public_key()))
    monkeypatch.setenv("AEGIS_ENABLED", "true")
    monkeypatch.delenv("AEGIS_DEV_BYPASS_EMAIL", raising=False)
    from app.core import config as cfg
    cfg.get_settings.cache_clear()
    return priv


@pytest.mark.asyncio
async def test_me_via_password_jwt(isolated_data_root):
    await bootstrap()
    from app.main import app
    from app.services import auth_svc

    client = TestClient(app)
    creds = await auth_svc.password_login("admin", "admin123")
    token = creds["tokens"]["access_token"]

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["auth_role"] == "super_admin"
    assert body["auth_source"] == "password"


@pytest.mark.asyncio
async def test_me_via_aegis_header(isolated_data_root, aegis_keypair):
    await bootstrap()
    from app.main import app

    client = TestClient(app)
    header = _sign_aegis(
        {"cas:email": "zhangsan@xiaomi.com", "cas:name": "张三"},
        aegis_keypair,
    )
    r = client.get("/api/v1/auth/me", headers={"X-Proxy-UserDetail": header})
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["email"] == "zhangsan@xiaomi.com"
    assert body["auth_source"] == "aegis"


@pytest.mark.asyncio
async def test_aegis_admin_mapping(isolated_data_root, aegis_keypair, monkeypatch):
    monkeypatch.setenv("AEGIS_ADMIN_EMAILS", "boss@xiaomi.com")
    from app.core import config as cfg
    cfg.get_settings.cache_clear()

    await bootstrap()
    from app.main import app

    client = TestClient(app)
    header = _sign_aegis({"cas:email": "boss@xiaomi.com"}, aegis_keypair)
    r = client.get("/api/v1/auth/me", headers={"X-Proxy-UserDetail": header})
    assert r.status_code == 200
    assert r.json()["data"]["auth_role"] == "super_admin"


@pytest.mark.asyncio
async def test_me_requires_credential(isolated_data_root, monkeypatch):
    # Repo-level .env may set AEGIS_DEV_BYPASS_EMAIL; override via env var
    # (pydantic-settings gives env vars higher priority than env_file).
    monkeypatch.setenv("AEGIS_DEV_BYPASS_EMAIL", "")
    monkeypatch.setenv("AEGIS_PUBLIC_KEY", "")
    from app.core import config as cfg
    cfg.get_settings.cache_clear()

    await bootstrap()
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tampered_aegis_header_rejected(isolated_data_root, aegis_keypair):
    await bootstrap()
    from app.main import app

    client = TestClient(app)
    header = _sign_aegis({"cas:email": "a@xiaomi.com"}, aegis_keypair)
    payload_b64, sig_b64 = header.split(".")
    tampered = base64.b64encode(b'{"cas:email":"evil@xiaomi.com"}').decode()

    r = client.get(
        "/api/v1/auth/me",
        headers={"X-Proxy-UserDetail": f"{tampered}.{sig_b64}"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_methods_endpoint(isolated_data_root, aegis_keypair):
    await bootstrap()
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/v1/auth/methods")
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["aegis_enabled"] is True
    assert body["password_enabled"] is True


@pytest.mark.asyncio
async def test_password_login_still_works_with_aegis_configured(
    isolated_data_root, aegis_keypair
):
    """Aegis being configured shouldn't block password login."""
    await bootstrap()
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "admin", "password": "admin123"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["tokens"]["access_token"]
