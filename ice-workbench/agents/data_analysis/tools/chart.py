import io
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import OUTPUT_DIR

plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


TOOL_DEFINITION = {
    "name": "generate_chart",
    "description": "Generate a chart image (PNG) from CSV data",
    "input_schema": {
        "type": "object",
        "properties": {
            "csv_content": {
                "type": "string",
                "description": "CSV data with header row",
            },
            "chart_type": {
                "type": "string",
                "enum": ["bar", "line", "pie", "heatmap", "scatter"],
            },
            "title": {"type": "string"},
            "x_column": {"type": "string"},
            "y_column": {"type": "string"},
            "topic": {
                "type": "string",
                "description": "Short topic name for the filename",
            },
        },
        "required": ["csv_content", "chart_type", "title", "x_column", "y_column", "topic"],
    },
}


def handle_generate_chart(
    csv_content: str,
    chart_type: str,
    title: str,
    x_column: str,
    y_column: str,
    topic: str,
) -> str:
    df = pd.read_csv(io.StringIO(csv_content))

    if x_column not in df.columns:
        return json.dumps({"error": f"Column '{x_column}' not found. Available: {list(df.columns)}"})
    if y_column not in df.columns:
        return json.dumps({"error": f"Column '{y_column}' not found. Available: {list(df.columns)}"})

    fig, ax = plt.subplots(figsize=(12, 6))

    if chart_type == "bar":
        ax.bar(df[x_column].astype(str), df[y_column])
    elif chart_type == "line":
        ax.plot(df[x_column].astype(str), df[y_column], marker="o")
    elif chart_type == "pie":
        ax.pie(df[y_column], labels=df[x_column].astype(str), autopct="%1.1f%%")
    elif chart_type == "scatter":
        ax.scatter(df[x_column], df[y_column])
    elif chart_type == "heatmap":
        pivot = df.pivot_table(values=y_column, index=df.columns[0], columns=df.columns[1] if len(df.columns) > 2 else df.columns[0])
        ax.imshow(pivot.values, aspect="auto")
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(pivot.index)

    ax.set_title(title, fontsize=14)
    if chart_type != "pie":
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        plt.xticks(rotation=45, ha="right")

    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c for c in topic if c.isalnum() or c in "-_").strip() or "chart"
    filename = f"{timestamp}_{safe_topic}_{chart_type}.png"
    filepath = OUTPUT_DIR / filename

    fig.savefig(filepath, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return json.dumps({
        "saved": True,
        "path": str(filepath.resolve()),
        "chart_type": chart_type,
    })
