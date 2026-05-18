import json
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR


TOOL_DEFINITION = {
    "name": "save_csv",
    "description": "Save query results to a local CSV file",
    "input_schema": {
        "type": "object",
        "properties": {
            "csv_content": {
                "type": "string",
                "description": "CSV content with header row",
            },
            "topic": {
                "type": "string",
                "description": "Short topic name for the filename",
            },
        },
        "required": ["csv_content", "topic"],
    },
}


def handle_save_csv(csv_content: str, topic: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c for c in topic if c.isalnum() or c in "-_").strip() or "data"
    filename = f"{timestamp}_{safe_topic}.csv"
    filepath = OUTPUT_DIR / filename

    filepath.write_text(csv_content, encoding="utf-8")

    return json.dumps({
        "saved": True,
        "path": str(filepath.resolve()),
        "rows": csv_content.count("\n"),
    })
