"""Unified error envelope and error_code enum (SHARED.md §6, §7)."""
from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


class ErrorCode:
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    SUPER_ADMIN_REQUIRES_FEISHU = "SUPER_ADMIN_REQUIRES_FEISHU"
    FEISHU_ACCOUNT_NOT_WHITELISTED = "FEISHU_ACCOUNT_NOT_WHITELISTED"
    FEISHU_BINDING_CONFLICT = "FEISHU_BINDING_CONFLICT"
    FEISHU_NOT_CONFIGURED = "FEISHU_NOT_CONFIGURED"
    LOGIN_RATE_LIMITED = "LOGIN_RATE_LIMITED"
    OPEN_REGISTER_DISABLED = "OPEN_REGISTER_DISABLED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_REFRESH_FAILED = "TOKEN_REFRESH_FAILED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    TOOL_TIMEOUT = "TOOL_TIMEOUT_30s"
    LLM_KEY_MISSING = "LLM_KEY_MISSING"
    LLM_BUDGET_EXCEEDED = "LLM_BUDGET_EXCEEDED"
    KB_SYNC_FAILED = "KB_SYNC_FAILED"
    KYUUBI_NOT_CONFIGURED = "KYUUBI_NOT_CONFIGURED"
    LAST_SUPER_ADMIN_PROTECTED = "LAST_SUPER_ADMIN_PROTECTED"
    CANNOT_DEMOTE_SELF = "CANNOT_DEMOTE_SELF"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    # Task workspace
    CONVERSATION_INFLIGHT = "CONVERSATION_INFLIGHT"
    JOIN_ALREADY_PENDING = "JOIN_ALREADY_PENDING"
    JOIN_ALREADY_MEMBER = "JOIN_ALREADY_MEMBER"
    AGENT_SNAPSHOT_STALE = "AGENT_SNAPSHOT_STALE"
    IMPORT_SOURCE_NOT_SUPPORTED = "IMPORT_SOURCE_NOT_SUPPORTED"
    IMPORT_SOURCE_NOT_ACCESSIBLE = "IMPORT_SOURCE_NOT_ACCESSIBLE"
    IMPORT_DUPLICATE = "IMPORT_DUPLICATE"
    IMPORT_FETCH_FAILED = "IMPORT_FETCH_FAILED"
    FEISHU_DISABLED = "FEISHU_DISABLED"
    FILE_REFRESH_FORBIDDEN = "FILE_REFRESH_FORBIDDEN"
    CARD_STATUS_IMMUTABLE = "CARD_STATUS_IMMUTABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIError(HTTPException):
    """Raise to return SHARED.md §7 envelope automatically."""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        detail: Any = None,
        biz_code: int | None = None,
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.message = message
        self.biz_code = biz_code if biz_code is not None else status_code * 100 + 1
        self.extra = detail

    def to_envelope(self) -> dict:
        return {
            "code": self.biz_code,
            "message": self.message,
            "error_code": self.error_code,
            "data": self.extra,
        }


def ok(data: Any = None, message: str = "success") -> dict:
    return {"code": 0, "message": message, "data": data}


def page(items: list, total: int, page_no: int = 1, page_size: int = 15) -> dict:
    return ok({"items": items, "total": total, "page": page_no, "page_size": page_size})


def err_permission(detail: str = "permission denied") -> APIError:
    return APIError(status.HTTP_403_FORBIDDEN, ErrorCode.PERMISSION_DENIED, detail)


def err_not_found(detail: str = "not found") -> APIError:
    return APIError(status.HTTP_404_NOT_FOUND, ErrorCode.RESOURCE_NOT_FOUND, detail)
