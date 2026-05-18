import json
import subprocess
import tempfile
from pathlib import Path


TOOL_DEFINITION = {
    "name": "publish_to_feishu",
    "description": "Create a Feishu document with the analysis report and return the document URL",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Document title"},
            "markdown_content": {
                "type": "string",
                "description": "Report content in Feishu extended markdown",
            },
        },
        "required": ["title", "markdown_content"],
    },
}


def handle_publish_to_feishu(title: str, markdown_content: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(markdown_content)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["feishu", "docx", "create", title, "-f", tmp_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    # exit code 2 = partial success (doc created but content failed)
    # exit code 3 = success with warnings (e.g. mermaid render failed)
    # both still return a valid doc_token in stdout
    if result.returncode not in (0, 2, 3):
        return json.dumps({"error": result.stderr.strip() or f"feishu exited with code {result.returncode}"})

    try:
        data = json.loads(result.stdout)
        url = data.get("url", "")
        doc_token = data.get("doc_token", "")
        return json.dumps({"url": url, "doc_token": doc_token, "title": title})
    except json.JSONDecodeError:
        return json.dumps({"raw_output": result.stdout.strip()})
