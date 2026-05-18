"""Round-trip test for 米盾 (Aegis) X-Proxy-UserDetail verification.

We don't have the production public key here; instead we generate a keypair,
sign a synthetic payload with the private half, and verify with the public half
through the same module the runtime uses.
"""
from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.core.aegis import AegisVerifyError, verify


def _make_header(payload: dict, private_key: rsa.RSAPrivateKey) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    sig = private_key.sign(data, padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(data).decode() + "." + base64.b64encode(sig).decode()


def _pub_b64(public_key: rsa.RSAPublicKey) -> str:
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return base64.b64encode(der).decode()


@pytest.fixture(scope="module")
def keypair() -> tuple[rsa.RSAPrivateKey, str]:
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return priv, _pub_b64(priv.public_key())


def test_verify_happy_path(keypair):
    priv, pub_b64 = keypair
    payload = {
        "cas:uid": "10001",
        "cas:user": "zhangsan",
        "cas:name": "张三",
        "cas:displayName": "sa zhang 张三",
        "cas:departmentName": "信息安全与隐私",
        "cas:email": "zhangsan@xiaomi.com",
        "cas:type": "employee",
        "cas:miID": "mi-10001",
        "cas:avatar": "https://example.com/a.png",
    }
    header = _make_header(payload, priv)
    info = verify(header, [pub_b64])
    assert info.email == "zhangsan@xiaomi.com"
    assert info.name == "张三"
    assert info.department_name == "信息安全与隐私"
    assert info.uid == "10001"
    assert info.type == "employee"


def test_verify_rejects_tampered_payload(keypair):
    priv, pub_b64 = keypair
    header = _make_header({"cas:email": "a@xiaomi.com"}, priv)
    payload_b64, sig_b64 = header.split(".")
    tampered = base64.b64encode(b'{"cas:email":"admin@xiaomi.com"}').decode()
    with pytest.raises(AegisVerifyError):
        verify(f"{tampered}.{sig_b64}", [pub_b64])


def test_verify_rejects_bad_key(keypair):
    priv, _ = keypair
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    header = _make_header({"cas:email": "a@xiaomi.com"}, priv)
    with pytest.raises(AegisVerifyError):
        verify(header, [_pub_b64(other.public_key())])


def test_verify_multi_key_rotation(keypair):
    """Rotation: new key listed first, old key still valid."""
    priv, pub_b64 = keypair
    new_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    new_pub = _pub_b64(new_priv.public_key())
    header = _make_header({"cas:email": "a@xiaomi.com"}, priv)
    info = verify(header, [new_pub, pub_b64])
    assert info.email == "a@xiaomi.com"


def test_verify_malformed_header(keypair):
    _, pub_b64 = keypair
    with pytest.raises(AegisVerifyError):
        verify("not-a-valid-header", [pub_b64])
    with pytest.raises(AegisVerifyError):
        verify("", [pub_b64])


def test_verify_no_keys_configured(keypair):
    priv, _ = keypair
    header = _make_header({"cas:email": "a@xiaomi.com"}, priv)
    with pytest.raises(AegisVerifyError):
        verify(header, [])


def test_verify_accepts_pem_key(keypair):
    priv, _ = keypair
    pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    header = _make_header({"cas:email": "a@xiaomi.com"}, priv)
    info = verify(header, [pem])
    assert info.email == "a@xiaomi.com"
