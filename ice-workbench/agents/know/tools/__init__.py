"""Knowledge agent tools — wrapping feishu CLI and mify scripts."""
from __future__ import annotations

import json
import subprocess
import logging

logger = logging.getLogger(__name__)

FEISHU_CLI = "feishu"
MIFY_SKILL_DIR = "~/.trae-cn/skills/mify-knowledge-base"
DEFAULT_KB = "数据产品知识库beta"


def handle_feishu_read(url: str) -> str:
    try:
        result = subprocess.run(
            [FEISHU_CLI, "fetch", url],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode in (0, 2, 3):
            return json.dumps({"success": True, "content": result.stdout[:10000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "feishu fetch timed out"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "feishu CLI not installed"})


def handle_feishu_write(title: str, content: str, parent_node: str = "") -> str:
    cmd = [FEISHU_CLI, "docx", "create", title, "-c", content]
    if parent_node:
        cmd.extend(["--wiki-node", parent_node])
    else:
        cmd.extend(["--wiki-space", "7631112709378935772"])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode in (0, 2, 3):
            return json.dumps({"success": True, "output": result.stdout[:2000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "feishu write timed out"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "feishu CLI not installed"})


def handle_feishu_search(query: str) -> str:
    try:
        result = subprocess.run(
            [FEISHU_CLI, "search", query],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode in (0, 2, 3):
            return json.dumps({"success": True, "results": result.stdout[:5000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "feishu search timed out"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "feishu CLI not installed"})


def handle_mify_search(query: str, kb_name: str = DEFAULT_KB, top_k: int = 5) -> str:
    import os
    skill_dir = os.path.expanduser(MIFY_SKILL_DIR)
    script = f"{skill_dir}/scripts/search_knowledge_base.py"
    try:
        result = subprocess.run(
            ["python3", script, "--kb", kb_name, "--query", query, "--top-k", str(top_k)],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return json.dumps({"success": True, "results": result.stdout[:5000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "mify search timed out"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "mify script not found"})


def handle_mify_upload(kb_name: str, file_path: str) -> str:
    import os
    skill_dir = os.path.expanduser(MIFY_SKILL_DIR)
    script = f"{skill_dir}/scripts/create_documents.py"
    try:
        result = subprocess.run(
            ["python3", script, "local", "--kb", kb_name, "--dir", file_path],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            return json.dumps({"success": True, "output": result.stdout[:2000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "mify upload timed out"})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "mify script not found"})
