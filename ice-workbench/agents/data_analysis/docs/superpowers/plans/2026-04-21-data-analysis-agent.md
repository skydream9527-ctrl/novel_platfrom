# Data Analysis Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a multi-phase data analysis agent that takes natural language questions, generates SQL via nl-sql skill, executes via Kyuubi, produces CSV + charts, runs 3-expert analysis, and publishes to Feishu.

**Architecture:** Single Python orchestrator (`agent.py`) with tool_use loop. Tools wrap `kyuubi` CLI (execution), `nl-sql` skill (SQL generation), Matplotlib (charts), and `feishu` CLI (document publishing). Multi-agent analysis uses parallel `messages.create()` calls with role-specific system prompts. All state is in-memory conversation history.

**Tech Stack:** Python 3.11+, `anthropic` SDK, `matplotlib`, `pandas`, `kyuubi-cli`, `feishu` CLI

---

## Prerequisites: Install Kyuubi Skill

Before starting implementation, the Kyuubi CLI must be installed:

```bash
git clone https://git.n.xiaomi.com/olap/xcode.git /tmp/xcode
npx skills add /tmp/xcode/skills/kyuubi
kyuubi config init
# Edit ~/.kyuubi/config.yml with workspace_id and token
```

Verify: `kyuubi --version`

---

## File Structure

```
data_analysis/
├── agent.py                  # Main entry point — orchestrator agent loop + tool dispatch
├── config.py                 # All configuration: paths, model names, business lines
├── tools/
│   ├── __init__.py           # Exports all tool definitions and handlers
│   ├── nlsql.py              # Wraps nl-sql skill: reads reference files, builds SQL
│   ├── kyuubi.py             # Wraps kyuubi CLI: execute_query, list_tables, describe
│   ├── csv_export.py         # Save pandas DataFrame to CSV
│   ├── chart.py              # Matplotlib chart generation from DataFrame
│   └── feishu.py             # Wraps feishu CLI: create doc, return URL
├── experts/
│   ├── __init__.py           # Exports run_expert_analysis()
│   ├── prompts.py            # System prompts for all 3 expert roles
│   └── runner.py             # Async expert execution: parallel + sequential merge
├── nl-sql/                   # (existing) nl-sql skill — SQL generation source of truth
│   ├── SKILL.md
│   ├── scripts/nl-sql.py
│   └── reference/...
├── output/                   # Generated CSV + chart files (gitignored)
├── requirements.txt
└── .gitignore
```

---

### Task 1: Project Scaffolding + Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `config.py`
- Create: `tools/__init__.py`
- Create: `experts/__init__.py`
- Create: `output/` (directory)

- [ ] **Step 1: Create requirements.txt**

```
anthropic>=0.42.0
matplotlib>=3.8.0
pandas>=2.1.0
```

- [ ] **Step 2: Create .gitignore**

```
output/
__pycache__/
*.pyc
.env
*.egg-info/
.venv/
```

- [ ] **Step 3: Create config.py**

```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
NLSQL_DIR = PROJECT_ROOT / "nl-sql"
NLSQL_REFERENCE_DIR = NLSQL_DIR / "reference"
NLSQL_SCRIPT = NLSQL_DIR / "scripts" / "nl-sql.py"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True)

BUSINESS_LINES = {
    "browser-main": {
        "name": "浏览器主端",
        "reference_dir": "browser-main",
    },
    "browser-feed": {
        "name": "浏览器信息流",
        "reference_dir": "browser-feed",
    },
    "content-center": {
        "name": "内容中心",
        "reference_dir": "content-center",
    },
    "search": {
        "name": "搜索",
        "reference_dir": "search",
    },
    "novel": {
        "name": "小说",
        "reference_dir": "novel",
    },
}

MODEL_MAIN = "claude-sonnet-4-6"
MODEL_EXPERT = "claude-sonnet-4-6"
```

- [ ] **Step 4: Create empty __init__.py files**

Create `tools/__init__.py` and `experts/__init__.py` as empty files.

- [ ] **Step 5: Create output directory and install dependencies**

Run:
```bash
mkdir -p output
pip install -r requirements.txt
```

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore config.py tools/__init__.py experts/__init__.py
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: nl-sql Tool Wrapper

**Files:**
- Create: `tools/nlsql.py`
- Test: manual verification via `python -c "from tools.nlsql import ..."`

The nl-sql tool reads reference files from disk and constructs SQL following the three-element model (business line + metric + dimensions). It calls `nl-sql/scripts/nl-sql.py` to save the SQL file.

- [ ] **Step 1: Create tools/nlsql.py**

```python
import subprocess
import sys
from pathlib import Path

from config import NLSQL_REFERENCE_DIR, NLSQL_SCRIPT


def load_reference_file(business_line: str, filename: str) -> str:
    path = NLSQL_REFERENCE_DIR / business_line / filename
    if not path.exists():
        raise FileNotFoundError(f"Reference file not found: {path}")
    return path.read_text(encoding="utf-8")


def load_metric_index(business_line: str) -> str:
    return load_reference_file(business_line, "metric-name-index.md")


def load_dimension_index(business_line: str) -> str:
    return load_reference_file(business_line, "metric-dimension-index.md")


def load_table_schema(business_line: str) -> str:
    return load_reference_file(business_line, "core-metrics-tables.md")


def load_event_index(business_line: str) -> str:
    return load_reference_file(business_line, "event-name-index.md")


def load_event_reference(business_line: str) -> str:
    return load_reference_file(business_line, "event-metrics-reference.md")


def load_core_metrics_reference(business_line: str) -> str:
    return load_reference_file(business_line, "core-metrics-reference.md")


def save_sql_file(metric_name: str, sql: str, output_dir: str | None = None) -> str:
    cmd = [
        sys.executable, str(NLSQL_SCRIPT),
        "--metric", metric_name,
        "--sql", sql,
    ]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()


TOOL_DEFINITION = {
    "name": "generate_sql_via_nlsql",
    "description": (
        "Generate SQL using nl-sql skill reference files. "
        "Returns reference data (metric index, dimension index, table schema, "
        "event index) for the specified business line and data type. "
        "The agent MUST use this data to construct SQL following nl-sql's "
        "three-element model. This is the ONLY permitted way to produce SQL."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "business_line": {
                "type": "string",
                "enum": ["browser-main", "browser-feed", "content-center", "search", "novel"],
                "description": "Which business line to query",
            },
            "data_type": {
                "type": "string",
                "enum": ["core-metrics", "event-tracking"],
                "description": "Core metrics or event tracking",
            },
        },
        "required": ["business_line", "data_type"],
    },
}


def handle_generate_sql(business_line: str, data_type: str) -> str:
    parts = []

    if data_type == "core-metrics":
        parts.append("## Metric Name Index\n\n" + load_metric_index(business_line))
        parts.append("## Dimension Index\n\n" + load_dimension_index(business_line))
        parts.append("## Table Schema & SQL Templates\n\n" + load_table_schema(business_line))
        parts.append("## Core Metrics Reference\n\n" + load_core_metrics_reference(business_line))
    else:
        parts.append("## Event Name Index\n\n" + load_event_index(business_line))
        parts.append("## Event Metrics Reference\n\n" + load_event_reference(business_line))
        parts.append("## Table Schema\n\n" + load_table_schema(business_line))

    return "\n\n---\n\n".join(parts)
```

- [ ] **Step 2: Verify import works**

Run:
```bash
cd /Users/mi/Desktop/agents/data_analysis
python -c "from tools.nlsql import handle_generate_sql, TOOL_DEFINITION; print(TOOL_DEFINITION['name'])"
```

Expected: `generate_sql_via_nlsql`

- [ ] **Step 3: Commit**

```bash
git add tools/nlsql.py
git commit -m "feat: add nl-sql tool wrapper for reference file loading"
```

---

### Task 3: Kyuubi Tool Wrapper

**Files:**
- Create: `tools/kyuubi.py`

- [ ] **Step 1: Create tools/kyuubi.py**

```python
import json
import subprocess


def execute_query(sql: str) -> dict:
    result = subprocess.run(
        ["kyuubi", "sql", "query", sql],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip() or f"kyuubi exited with code {result.returncode}"}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw_output": result.stdout.strip()}


TOOL_DEFINITION = {
    "name": "execute_query",
    "description": (
        "Execute a SQL query via Kyuubi against Iceberg tables. "
        "The SQL MUST have been generated by the nl-sql skill — never hand-written. "
        "Only SELECT queries are allowed."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": "SQL query generated by nl-sql skill",
            },
        },
        "required": ["sql"],
    },
}


def handle_execute_query(sql: str) -> str:
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("SHOW") and not sql_upper.startswith("DESCRIBE"):
        return json.dumps({"error": "Only SELECT/SHOW/DESCRIBE queries are allowed"})

    result = execute_query(sql)
    return json.dumps(result, ensure_ascii=False, default=str)
```

- [ ] **Step 2: Commit**

```bash
git add tools/kyuubi.py
git commit -m "feat: add kyuubi CLI wrapper for query execution"
```

---

### Task 4: CSV Export Tool

**Files:**
- Create: `tools/csv_export.py`

- [ ] **Step 1: Create tools/csv_export.py**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add tools/csv_export.py
git commit -m "feat: add CSV export tool"
```

---

### Task 5: Chart Generation Tool

**Files:**
- Create: `tools/chart.py`

- [ ] **Step 1: Create tools/chart.py**

```python
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
```

- [ ] **Step 2: Verify matplotlib works**

Run:
```bash
python -c "
from tools.chart import handle_generate_chart
result = handle_generate_chart('x,y\n1,10\n2,20\n3,15', 'line', 'Test', 'x', 'y', 'test')
print(result)
"
```

Expected: JSON with `"saved": true` and a valid path.

- [ ] **Step 3: Commit**

```bash
git add tools/chart.py
git commit -m "feat: add Matplotlib chart generation tool"
```

---

### Task 6: Feishu Document Tool

**Files:**
- Create: `tools/feishu.py`

- [ ] **Step 1: Create tools/feishu.py**

```python
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

    if result.returncode != 0:
        return json.dumps({"error": result.stderr.strip() or f"feishu exited with code {result.returncode}"})

    try:
        data = json.loads(result.stdout)
        url = data.get("url", "")
        doc_token = data.get("doc_token", "")
        return json.dumps({"url": url, "doc_token": doc_token, "title": title})
    except json.JSONDecodeError:
        return json.dumps({"raw_output": result.stdout.strip()})
```

- [ ] **Step 2: Commit**

```bash
git add tools/feishu.py
git commit -m "feat: add Feishu document creation tool"
```

---

### Task 7: Tool Registry

**Files:**
- Modify: `tools/__init__.py`

- [ ] **Step 1: Update tools/__init__.py**

```python
from tools.nlsql import TOOL_DEFINITION as NLSQL_TOOL, handle_generate_sql
from tools.kyuubi import TOOL_DEFINITION as KYUUBI_TOOL, handle_execute_query
from tools.csv_export import TOOL_DEFINITION as CSV_TOOL, handle_save_csv
from tools.chart import TOOL_DEFINITION as CHART_TOOL, handle_generate_chart
from tools.feishu import TOOL_DEFINITION as FEISHU_TOOL, handle_publish_to_feishu

ALL_TOOLS = [NLSQL_TOOL, KYUUBI_TOOL, CSV_TOOL, CHART_TOOL, FEISHU_TOOL]

TOOL_HANDLERS = {
    "generate_sql_via_nlsql": lambda args: handle_generate_sql(
        business_line=args["business_line"],
        data_type=args["data_type"],
    ),
    "execute_query": lambda args: handle_execute_query(sql=args["sql"]),
    "save_csv": lambda args: handle_save_csv(
        csv_content=args["csv_content"],
        topic=args["topic"],
    ),
    "generate_chart": lambda args: handle_generate_chart(
        csv_content=args["csv_content"],
        chart_type=args["chart_type"],
        title=args["title"],
        x_column=args["x_column"],
        y_column=args["y_column"],
        topic=args["topic"],
    ),
    "publish_to_feishu": lambda args: handle_publish_to_feishu(
        title=args["title"],
        markdown_content=args["markdown_content"],
    ),
}
```

- [ ] **Step 2: Verify all imports**

Run:
```bash
python -c "from tools import ALL_TOOLS, TOOL_HANDLERS; print(f'{len(ALL_TOOLS)} tools, {len(TOOL_HANDLERS)} handlers')"
```

Expected: `5 tools, 5 handlers`

- [ ] **Step 3: Commit**

```bash
git add tools/__init__.py
git commit -m "feat: add tool registry with all handlers"
```

---

### Task 8: Expert System Prompts

**Files:**
- Create: `experts/prompts.py`

- [ ] **Step 1: Create experts/prompts.py**

```python
SQL_ENGINEER_PROMPT = """\
你是一名资深 SQL 工程师，专注于数据质量和查询正确性。

你的职责：
1. 评估数据质量：检查结果中的空值、异常值、重复数据
2. 验证查询口径：SQL 的过滤条件和聚合逻辑是否与指标定义一致
3. 数据口径说明：解释数据的来源、统计口径、可能的偏差
4. 补充查询建议：如果数据不完整或需要交叉验证，建议补充查询

输出格式：
## 数据质量评估
（空值比例、异常值、数据完整性）

## 查询口径说明
（数据来源、过滤逻辑、聚合方式）

## 补充建议
（如有必要的补充查询或交叉验证建议）
"""

DATA_ANALYST_PROMPT = """\
你是一名资深数据分析师，擅长从数据中发现洞察。

你的职责：
1. 统计特征描述：均值、中位数、标准差、分布特征
2. 趋势分析：识别上升/下降/波动趋势，拐点分析
3. 异常检测：标记显著偏离正常范围的数据点
4. 相关性分析：不同维度间的关联关系
5. 同比/环比分析：如果数据支持，给出时间维度的对比

输出格式：
## 关键发现
（最重要的 3-5 个发现，按重要性排序）

## 统计概览
（核心统计指标）

## 趋势与异常
（趋势描述、异常标记）

## 深入分析
（维度拆解、相关性、对比分析）
"""

BUSINESS_ADVISOR_PROMPT = """\
你是一名资深互联网业务顾问，精通浏览器和信息流产品。

你的职责：
1. 业务含义解读：将数据发现翻译为业务语言
2. 归因分析：数据变化可能由什么业务动作导致
3. 可行动建议：基于数据给出具体的产品/运营建议
4. 风险提示：数据中暗示的潜在风险

输出格式：
## 核心结论
（用业务语言总结最重要的发现）

## 业务解读
（数据变化的业务含义和可能原因）

## 行动建议
（具体的、可执行的建议，按优先级排序）

## 风险提示
（需要关注的风险信号）
"""

REPORT_MERGE_PROMPT = """\
你是一名高级分析报告编辑。你将收到三位专家的分析：SQL工程师（数据质量）、数据分析师（统计洞察）、业务顾问（业务解读）。

你的任务是将三方分析合并为一份结构完整、适合在飞书文档中发布的分析报告。

报告结构要求：
1. **摘要**：3-5 句话概括核心发现和建议
2. **数据概览**：查询的表、时间范围、数据量
3. **关键发现**：合并分析师和业务顾问的核心观点
4. **数据质量说明**：来自 SQL 工程师的评估
5. **业务建议**：来自业务顾问的行动建议
6. **附录**：使用的 SQL 查询

输出使用飞书扩展 Markdown 格式。使用表格展示数据，使用 Callout 块突出关键结论。
"""
```

- [ ] **Step 2: Commit**

```bash
git add experts/prompts.py
git commit -m "feat: add expert system prompts for 3 roles + report merger"
```

---

### Task 9: Expert Runner (Async Parallel Execution)

**Files:**
- Create: `experts/runner.py`
- Modify: `experts/__init__.py`

- [ ] **Step 1: Create experts/runner.py**

```python
import asyncio
import json

from anthropic import AsyncAnthropic

from config import MODEL_EXPERT
from experts.prompts import (
    SQL_ENGINEER_PROMPT,
    DATA_ANALYST_PROMPT,
    BUSINESS_ADVISOR_PROMPT,
    REPORT_MERGE_PROMPT,
)

client = AsyncAnthropic()


async def run_expert(role_name: str, system_prompt: str, context: str) -> dict:
    response = await client.messages.create(
        model=MODEL_EXPERT,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": context}],
    )
    return {
        "role": role_name,
        "analysis": response.content[0].text,
    }


async def run_expert_analysis(
    sql_used: str,
    csv_data: str,
    chart_paths: list[str],
    analysis_brief: str,
) -> dict:
    shared_context = (
        f"## 分析目标\n\n{analysis_brief}\n\n"
        f"## 使用的 SQL\n\n```sql\n{sql_used}\n```\n\n"
        f"## 查询结果数据（CSV）\n\n```csv\n{csv_data}\n```\n\n"
        f"## 生成的图表\n\n" + "\n".join(f"- {p}" for p in chart_paths)
    )

    sql_engineer_task = run_expert("SQL工程师", SQL_ENGINEER_PROMPT, shared_context)
    data_analyst_task = run_expert("数据分析师", DATA_ANALYST_PROMPT, shared_context)

    sql_result, analyst_result = await asyncio.gather(sql_engineer_task, data_analyst_task)

    advisor_context = (
        shared_context
        + f"\n\n## 数据分析师的初步发现\n\n{analyst_result['analysis']}"
    )
    advisor_result = await run_expert("业务顾问", BUSINESS_ADVISOR_PROMPT, advisor_context)

    return {
        "sql_engineer": sql_result["analysis"],
        "data_analyst": analyst_result["analysis"],
        "business_advisor": advisor_result["analysis"],
    }


async def merge_expert_reports(
    expert_outputs: dict,
    sql_used: str,
    analysis_brief: str,
) -> str:
    merge_context = (
        f"## 分析目标\n\n{analysis_brief}\n\n"
        f"## SQL 工程师分析\n\n{expert_outputs['sql_engineer']}\n\n"
        f"## 数据分析师分析\n\n{expert_outputs['data_analyst']}\n\n"
        f"## 业务顾问分析\n\n{expert_outputs['business_advisor']}\n\n"
        f"## 使用的 SQL\n\n```sql\n{sql_used}\n```"
    )

    response = await client.messages.create(
        model=MODEL_EXPERT,
        max_tokens=8192,
        system=REPORT_MERGE_PROMPT,
        messages=[{"role": "user", "content": merge_context}],
    )
    return response.content[0].text
```

- [ ] **Step 2: Update experts/__init__.py**

```python
from experts.runner import run_expert_analysis, merge_expert_reports
```

- [ ] **Step 3: Commit**

```bash
git add experts/runner.py experts/__init__.py
git commit -m "feat: add async expert runner with parallel execution"
```

---

### Task 10: Main Agent Orchestrator

**Files:**
- Create: `agent.py`

This is the core agent loop: manages conversation history, dispatches tool calls, and orchestrates all phases.

- [ ] **Step 1: Create agent.py**

```python
import asyncio
import json
import sys

from anthropic import Anthropic

from config import MODEL_MAIN
from tools import ALL_TOOLS, TOOL_HANDLERS
from experts.runner import run_expert_analysis, merge_expert_reports

SYSTEM_PROMPT = """\
你是一名专业的数据分析 Agent，帮助用户分析浏览器和信息流业务数据。

## 工作流程

### Phase 1: 需求澄清
通过多轮对话明确用户的分析需求：
- 业务线（浏览器主端/信息流/内容中心/搜索/小说）
- 数据类型（核心指标/埋点数据）
- 指标名称、维度、时间范围
- 获得用户明确确认后再继续

### Phase 2: SQL 生成
**必须使用 generate_sql_via_nlsql 工具获取参考文件，然后根据 nl-sql 的三要素模型生成 SQL。**
**禁止直接手写 SQL，所有 SQL 必须基于 nl-sql 参考文件生成。**
遵循 nl-sql 的自检清单：日期格式 YYYYMMDD、字段合法性、表名三段式前缀、分区过滤。

### Phase 3: 数据查询与可视化
- 使用 execute_query 执行 SQL
- 使用 save_csv 保存结果
- 使用 generate_chart 生成适合数据的图表

### Phase 4: 多专家分析
查询完成后，告诉用户 "数据已获取，正在启动多专家分析..."。
系统会自动调用 SQL工程师、数据分析师、业务顾问进行并行分析。

### Phase 5: 发布
使用 publish_to_feishu 将完整分析报告写入飞书文档，打印链接。

## 重要规则
- SQL 只能通过 nl-sql skill 生成，不能手写
- 每次查询前展示 SQL 给用户确认
- 图表类型根据数据特征自动选择
"""

client = Anthropic()


def run_agent():
    messages = []
    analysis_state = {
        "sql_used": "",
        "csv_data": "",
        "chart_paths": [],
        "analysis_brief": "",
    }

    print("数据分析 Agent 已启动。请输入你的分析需求（输入 quit 退出）\n")

    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            print("再见！")
            break

        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        while True:
            response = client.messages.create(
                model=MODEL_MAIN,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                tools=ALL_TOOLS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                text_parts = [b.text for b in response.content if b.type == "text"]
                assistant_text = "\n".join(text_parts)
                messages.append({"role": "assistant", "content": response.content})
                print(f"\nAgent: {assistant_text}\n")
                break

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    tool_name = block.name
                    tool_input = block.input

                    print(f"  [调用工具: {tool_name}]")

                    handler = TOOL_HANDLERS.get(tool_name)
                    if handler is None:
                        result_text = json.dumps({"error": f"Unknown tool: {tool_name}"})
                    else:
                        try:
                            result_text = handler(tool_input)
                        except Exception as e:
                            result_text = json.dumps({"error": str(e)})

                    if tool_name == "execute_query":
                        analysis_state["sql_used"] = tool_input.get("sql", "")
                        try:
                            data = json.loads(result_text)
                            if "raw_output" in data:
                                analysis_state["csv_data"] = data["raw_output"]
                        except (json.JSONDecodeError, KeyError):
                            pass

                    if tool_name == "save_csv":
                        analysis_state["csv_data"] = tool_input.get("csv_content", "")

                    if tool_name == "generate_chart":
                        try:
                            data = json.loads(result_text)
                            if data.get("saved"):
                                analysis_state["chart_paths"].append(data["path"])
                        except (json.JSONDecodeError, KeyError):
                            pass

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })

                messages.append({"role": "user", "content": tool_results})

                # Check if we should trigger expert analysis
                text_parts = [b.text for b in response.content if b.type == "text"]
                combined_text = " ".join(text_parts)
                if "多专家分析" in combined_text or "专家分析" in combined_text:
                    print("\n  [启动多专家并行分析...]")
                    analysis_state["analysis_brief"] = combined_text

                    expert_outputs = asyncio.run(
                        run_expert_analysis(
                            sql_used=analysis_state["sql_used"],
                            csv_data=analysis_state["csv_data"],
                            chart_paths=analysis_state["chart_paths"],
                            analysis_brief=analysis_state["analysis_brief"],
                        )
                    )

                    print("  [SQL工程师 ✓] [数据分析师 ✓] [业务顾问 ✓]")

                    merged_report = asyncio.run(
                        merge_expert_reports(
                            expert_outputs=expert_outputs,
                            sql_used=analysis_state["sql_used"],
                            analysis_brief=analysis_state["analysis_brief"],
                        )
                    )

                    print("  [分析报告已合并]")

                    messages.append({
                        "role": "user",
                        "content": (
                            "多专家分析已完成，以下是合并后的分析报告。"
                            "请使用 publish_to_feishu 工具将此报告发布到飞书文档，"
                            "然后将飞书文档链接展示给用户。\n\n"
                            f"{merged_report}"
                        ),
                    })

                continue

            else:
                text_parts = [b.text for b in response.content if b.type == "text"]
                if text_parts:
                    print(f"\nAgent: {' '.join(text_parts)}\n")
                messages.append({"role": "assistant", "content": response.content})
                break


if __name__ == "__main__":
    run_agent()
```

- [ ] **Step 2: Verify agent imports and starts**

Run:
```bash
python -c "import agent; print('imports OK')"
```

Expected: `imports OK`

- [ ] **Step 3: Commit**

```bash
git add agent.py
git commit -m "feat: add main agent orchestrator with full pipeline"
```

---

### Task 11: Save SQL via nl-sql Script Integration

**Files:**
- Modify: `tools/nlsql.py` (add save_sql tool)
- Modify: `tools/__init__.py` (register new tool)

The agent needs a tool to save the generated SQL file using the nl-sql script after the user confirms the SQL.

- [ ] **Step 1: Add save tool definition to tools/nlsql.py**

Append to the end of `tools/nlsql.py`:

```python
SAVE_SQL_TOOL = {
    "name": "save_sql_file",
    "description": "Save generated SQL to a file using nl-sql script",
    "input_schema": {
        "type": "object",
        "properties": {
            "metric_name": {
                "type": "string",
                "description": "Metric name for the filename",
            },
            "sql": {
                "type": "string",
                "description": "SQL content to save",
            },
        },
        "required": ["metric_name", "sql"],
    },
}


def handle_save_sql(metric_name: str, sql: str) -> str:
    try:
        output = save_sql_file(metric_name, sql)
        return output
    except subprocess.CalledProcessError as e:
        return f"Error saving SQL: {e.stderr}"
```

- [ ] **Step 2: Update tools/__init__.py to include save_sql**

```python
from tools.nlsql import (
    TOOL_DEFINITION as NLSQL_TOOL,
    SAVE_SQL_TOOL,
    handle_generate_sql,
    handle_save_sql,
)
from tools.kyuubi import TOOL_DEFINITION as KYUUBI_TOOL, handle_execute_query
from tools.csv_export import TOOL_DEFINITION as CSV_TOOL, handle_save_csv
from tools.chart import TOOL_DEFINITION as CHART_TOOL, handle_generate_chart
from tools.feishu import TOOL_DEFINITION as FEISHU_TOOL, handle_publish_to_feishu

ALL_TOOLS = [NLSQL_TOOL, SAVE_SQL_TOOL, KYUUBI_TOOL, CSV_TOOL, CHART_TOOL, FEISHU_TOOL]

TOOL_HANDLERS = {
    "generate_sql_via_nlsql": lambda args: handle_generate_sql(
        business_line=args["business_line"],
        data_type=args["data_type"],
    ),
    "save_sql_file": lambda args: handle_save_sql(
        metric_name=args["metric_name"],
        sql=args["sql"],
    ),
    "execute_query": lambda args: handle_execute_query(sql=args["sql"]),
    "save_csv": lambda args: handle_save_csv(
        csv_content=args["csv_content"],
        topic=args["topic"],
    ),
    "generate_chart": lambda args: handle_generate_chart(
        csv_content=args["csv_content"],
        chart_type=args["chart_type"],
        title=args["title"],
        x_column=args["x_column"],
        y_column=args["y_column"],
        topic=args["topic"],
    ),
    "publish_to_feishu": lambda args: handle_publish_to_feishu(
        title=args["title"],
        markdown_content=args["markdown_content"],
    ),
}
```

- [ ] **Step 3: Verify**

Run:
```bash
python -c "from tools import ALL_TOOLS, TOOL_HANDLERS; print(f'{len(ALL_TOOLS)} tools, {len(TOOL_HANDLERS)} handlers')"
```

Expected: `6 tools, 6 handlers`

- [ ] **Step 4: Commit**

```bash
git add tools/nlsql.py tools/__init__.py
git commit -m "feat: add save_sql_file tool for nl-sql script integration"
```

---

### Task 12: End-to-End Smoke Test

**Files:** None (manual verification)

- [ ] **Step 1: Verify all imports**

Run:
```bash
cd /Users/mi/Desktop/agents/data_analysis
python -c "
from tools import ALL_TOOLS, TOOL_HANDLERS
from experts import run_expert_analysis, merge_expert_reports
from config import BUSINESS_LINES, NLSQL_REFERENCE_DIR
import agent

print(f'Tools: {len(ALL_TOOLS)}')
print(f'Handlers: {len(TOOL_HANDLERS)}')
print(f'Business lines: {list(BUSINESS_LINES.keys())}')
print(f'Reference dir exists: {NLSQL_REFERENCE_DIR.exists()}')
print('All imports OK')
"
```

Expected:
```
Tools: 6
Handlers: 6
Business lines: ['browser-main', 'browser-feed', 'content-center', 'search', 'novel']
Reference dir exists: True
All imports OK
```

- [ ] **Step 2: Test nl-sql reference loading**

Run:
```bash
python -c "
from tools.nlsql import handle_generate_sql
result = handle_generate_sql('browser-main', 'core-metrics')
print(f'Reference data length: {len(result)} chars')
print('Contains metric index:', 'BM001' in result)
print('Contains table schema:', 'dwm_browser_event_aggregation' in result)
"
```

Expected:
```
Reference data length: <some number> chars
Contains metric index: True
Contains table schema: True
```

- [ ] **Step 3: Test chart generation**

Run:
```bash
python -c "
from tools.chart import handle_generate_chart
import json
result = handle_generate_chart(
    csv_content='date,dau\n20260401,1000\n20260402,1050\n20260403,980',
    chart_type='line',
    title='Browser DAU Trend',
    x_column='date',
    y_column='dau',
    topic='dau_trend',
)
data = json.loads(result)
print(f'Chart saved: {data[\"saved\"]}')
print(f'Path: {data[\"path\"]}')
"
```

Expected: `Chart saved: True` and a valid path in `output/`.

- [ ] **Step 4: Clean up test output**

Run:
```bash
rm -f output/*test* output/*dau_trend*
```

- [ ] **Step 5: Commit final state**

```bash
git add -A
git commit -m "feat: complete data analysis agent v1 — ready for testing"
```
