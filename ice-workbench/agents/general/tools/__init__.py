"""General agent tools — aggregates capabilities from all specialized agents."""
from __future__ import annotations

import json
import subprocess
import logging

logger = logging.getLogger(__name__)


def handle_query_data(sql: str, database: str = "default") -> str:
    """Execute SQL query via kyuubi-cli."""
    try:
        result = subprocess.run(
            ["kyuubi-cli", "query", "-e", sql],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            return json.dumps({"success": True, "result": result.stdout[:10000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "kyuubi-cli not installed"})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "query timed out"})


def handle_generate_chart(data: str, chart_type: str = "line", title: str = "图表") -> str:
    """Generate chart specification from data."""
    return json.dumps({
        "success": True,
        "result": {
            "chart_type": chart_type,
            "title": title,
            "data_preview": data[:500],
            "render_hint": "echart",
        },
    })


def handle_search_knowledge(query: str, source: str = "all") -> str:
    """Search across knowledge bases."""
    import os
    if source in ("mify", "all"):
        skill_dir = os.path.expanduser("~/.trae-cn/skills/mify-knowledge-base")
        script = f"{skill_dir}/scripts/search_knowledge_base.py"
        try:
            result = subprocess.run(
                ["python3", script, "--kb", "数据产品知识库beta", "--query", query, "--top-k", "5"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                return json.dumps({"success": True, "source": "mify", "results": result.stdout[:5000]})
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    if source in ("feishu", "all"):
        try:
            result = subprocess.run(
                ["feishu", "search", query],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode in (0, 2, 3):
                return json.dumps({"success": True, "source": "feishu", "results": result.stdout[:5000]})
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return json.dumps({"success": False, "error": "no knowledge base accessible"})


def handle_web_search(query: str) -> str:
    """Perform web search (placeholder for integration)."""
    return json.dumps({
        "success": True,
        "result": f"Web search for: {query}",
        "note": "Integrate with actual search API for production use",
    })


def handle_web_fetch(url: str) -> str:
    """Fetch web page content."""
    try:
        import httpx
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        content = resp.text[:8000]
        return json.dumps({"success": True, "content": content, "status": resp.status_code})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


def handle_create_document(title: str, content: str, format: str = "md") -> str:
    """Create a document (returns structured content for further processing)."""
    return json.dumps({
        "success": True,
        "result": {
            "title": title,
            "format": format,
            "content_length": len(content),
            "preview": content[:500],
        },
    })


def handle_feishu_read(url: str) -> str:
    """Read feishu document."""
    try:
        result = subprocess.run(
            ["feishu", "fetch", url],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode in (0, 2, 3):
            return json.dumps({"success": True, "content": result.stdout[:10000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "feishu CLI not installed"})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "feishu fetch timed out"})


def handle_feishu_publish(title: str, content: str) -> str:
    """Publish content to feishu wiki."""
    try:
        result = subprocess.run(
            ["feishu", "docx", "create", title, "-c", content, "--wiki-space", "7631112709378935772"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode in (0, 2, 3):
            return json.dumps({"success": True, "output": result.stdout[:2000]})
        return json.dumps({"success": False, "error": result.stderr[:500]})
    except FileNotFoundError:
        return json.dumps({"success": False, "error": "feishu CLI not installed"})
    except subprocess.TimeoutExpired:
        return json.dumps({"success": False, "error": "feishu publish timed out"})


def handle_anomaly_detect(data: str, metric: str, date_col: str = "date") -> str:
    """Detect anomalies in time series data."""
    return json.dumps({
        "success": True,
        "result": {
            "metric": metric,
            "anomaly_detected": False,
            "note": "Connect to analysis engine for full implementation",
        },
    })


def handle_trend_forecast(data: str, metric: str, days: int = 7) -> str:
    """Forecast time series trend."""
    return json.dumps({
        "success": True,
        "result": {
            "metric": metric,
            "forecast_days": days,
            "note": "Connect to analysis engine for full implementation",
        },
    })


def handle_period_compare(sql: str, compare_type: str, metric: str) -> str:
    """Compare metrics across periods."""
    return json.dumps({
        "success": True,
        "result": {
            "compare_type": compare_type,
            "metric": metric,
            "note": "Connect to data_analysis tools for full implementation",
        },
    })
