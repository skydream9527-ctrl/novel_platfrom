"""米盾 (Aegis) X-Proxy-UserDetail verification.

Format per aegis-java-sdk (AegisSignUtil.VerifySignGetInfo):
    <base64url_or_std(json_payload)>.<base64url_or_std(rsa_signature)>
Algorithm: SHA256withRSA. Public key: X.509 SubjectPublicKeyInfo, base64 DER.

Payload is a JSON object with keys like `cas:uid`, `cas:user`, `cas:name`,
`cas:type`, `cas:displayName`, `cas:departmentName`, `cas:email`, `cas:miID`,
`cas:avatar`.
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
from dataclasses import dataclass
from typing import Iterable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

log = logging.getLogger(__name__)


class AegisVerifyError(Exception):
    """Raised when X-Proxy-UserDetail cannot be verified."""


@dataclass(frozen=True)
class AegisUser:
    uid: str | None
    user: str | None
    name: str | None
    type: str | None
    display_name: str | None
    department_name: str | None
    email: str | None
    mi_id: str | None
    avatar: str | None

    @classmethod
    def from_payload(cls, payload: dict) -> "AegisUser":
        return cls(
            uid=payload.get("cas:uid"),
            user=payload.get("cas:user"),
            name=payload.get("cas:name"),
            type=payload.get("cas:type"),
            display_name=payload.get("cas:displayName"),
            department_name=payload.get("cas:departmentName"),
            email=payload.get("cas:email"),
            mi_id=payload.get("cas:miID"),
            avatar=payload.get("cas:avatar"),
        )


def _b64decode_tolerant(s: str) -> bytes:
    """Accept either standard or urlsafe base64, with or without padding."""
    s = s.strip()
    s_padded = s + "=" * (-len(s) % 4)
    try:
        return base64.urlsafe_b64decode(s_padded)
    except (binascii.Error, ValueError):
        return base64.b64decode(s_padded)


def _load_public_key(pem_or_b64: str) -> rsa.RSAPublicKey:
    """Accept either a full PEM ('-----BEGIN PUBLIC KEY-----' …) or raw base64 DER."""
    key = pem_or_b64.strip()
    if "-----BEGIN" in key:
        data = key.encode()
        pk = serialization.load_pem_public_key(data)
    else:
        der = base64.b64decode(key)
        pk = serialization.load_der_public_key(der)
    if not isinstance(pk, rsa.RSAPublicKey):
        raise AegisVerifyError("public key is not RSA")
    return pk


def verify(header_value: str, public_keys: Iterable[str]) -> AegisUser:
    """Verify X-Proxy-UserDetail and return the signed user info.

    Raises AegisVerifyError on any failure (bad format, no key matched, etc.).
    """
    if not header_value:
        raise AegisVerifyError("empty header")
    parts = header_value.split(".")
    if len(parts) != 2:
        raise AegisVerifyError("malformed header: expected <payload>.<signature>")
    payload_b64, sig_b64 = parts
    try:
        payload_bytes = _b64decode_tolerant(payload_b64)
        signature = _b64decode_tolerant(sig_b64)
    except (binascii.Error, ValueError) as e:
        raise AegisVerifyError(f"base64 decode failed: {e}") from e

    keys = [k for k in (s.strip() for s in public_keys) if k]
    if not keys:
        raise AegisVerifyError("no public key configured")

    last_err: Exception | None = None
    for key_str in keys:
        try:
            pk = _load_public_key(key_str)
            pk.verify(signature, payload_bytes, padding.PKCS1v15(), hashes.SHA256())
            break
        except InvalidSignature as e:
            last_err = e
            continue
        except Exception as e:  # malformed key etc — skip and try next
            last_err = e
            log.warning("aegis: skipping public key (%s)", e)
            continue
    else:
        raise AegisVerifyError(f"signature did not verify against any configured key: {last_err}")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise AegisVerifyError(f"payload is not JSON: {e}") from e
    if not isinstance(payload, dict):
        raise AegisVerifyError("payload is not a JSON object")
    return AegisUser.from_payload(payload)
