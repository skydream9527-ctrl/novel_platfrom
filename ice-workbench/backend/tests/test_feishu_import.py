from __future__ import annotations

import pytest

from app.core.errors import APIError, ErrorCode
from app.services import feishu_import_svc as svc


def test_parse_docx_url():
    ref = svc.parse_feishu_url("https://acme.feishu.cn/docx/ABCD1234?from=home")
    assert ref == {"obj_type": "docx", "obj_token": "ABCD1234"}


def test_parse_wiki_url():
    ref = svc.parse_feishu_url("https://acme.feishu.cn/wiki/WXYZ5678")
    assert ref == {"obj_type": "wiki", "obj_token": "WXYZ5678"}


def test_parse_rejects_non_feishu_host():
    with pytest.raises(APIError) as ei:
        svc.parse_feishu_url("https://evil.example.com/docx/ABCD1234")
    assert ei.value.error_code == ErrorCode.IMPORT_SOURCE_NOT_SUPPORTED


def test_parse_rejects_subdomain_feishu_lookalike():
    with pytest.raises(APIError):
        svc.parse_feishu_url("https://feishu.cn.evil.com/docx/X")


def test_parse_rejects_http_scheme():
    with pytest.raises(APIError):
        svc.parse_feishu_url("http://acme.feishu.cn/docx/ABCD1234")


def test_parse_unsupported_object_type():
    with pytest.raises(APIError):
        svc.parse_feishu_url("https://acme.feishu.cn/base/XYZ")
