"""Learn agent tools — wrapping shell scripts for research workflows."""
from __future__ import annotations

import json
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).resolve().parent / "ai-research-agent" / "scripts"


def handle_web_fetch(url: str) -> str:
    script = SCRIPTS_DIR / "fetch_web_page.sh"
    if not script.exists():
        return json.dumps({"success": False, "error": "fetch_web_page.sh not found"})
    try:
        result = subprocess.run(
            ["bash", str(script), url],
            capture_output=True, text=True, timeout=60,
            cwd=str(SCRIPTS_DIR.parent),
        )
        if result.returncode == 0:
            return json.dumps({"success": True, "content": result.stdout[:8000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "web fetch timed out"})


def handle_check_sources() -> str:
    script = SCRIPTS_DIR / "check_sources.sh"
    if not script.exists():
        return json.dumps({"success": False, "error": "check_sources.sh not found"})
    try:
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(SCRIPTS_DIR.parent),
        )
        if result.returncode == 0:
            return json.dumps({"success": True, "output": result.stdout[:5000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "source check timed out"})


def handle_generate_digest() -> str:
    script = SCRIPTS_DIR / "generate_weekly_digest.sh"
    if not script.exists():
        return json.dumps({"success": False, "error": "generate_weekly_digest.sh not found"})
    try:
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True, text=True, timeout=120,
            cwd=str(SCRIPTS_DIR.parent),
        )
        if result.returncode == 0:
            return json.dumps({"success": True, "digest": result.stdout[:8000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "digest generation timed out"})


def handle_import_links() -> str:
    script = SCRIPTS_DIR / "import_links.sh"
    if not script.exists():
        return json.dumps({"success": False, "error": "import_links.sh not found"})
    try:
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True, text=True, timeout=60,
            cwd=str(SCRIPTS_DIR.parent),
        )
        if result.returncode == 0:
            return json.dumps({"success": True, "output": result.stdout[:3000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "link import timed out"})
