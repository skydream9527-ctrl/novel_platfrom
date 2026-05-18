# Data Analysis Agent v2 Design Spec

## Overview

Upgrade of the existing data analysis agent (v1) to add deep analytical capabilities: an Analysis Engine that autonomously plans and executes supplementary queries, and a multi-round expert debate protocol that replaces the single-pass parallel analysis.

**Key improvements over v1:**
- Agent autonomously decides what to investigate after the initial query
- 5 new analysis tools (period comparison, dimension drilldown, anomaly detection, trend forecast, event correlation)
- Expert analysis becomes multi-round debate with challenge → response → arbiter verdict
- Feishu report reflects the debate process: consensus, disagreements, and reasoned final recommendation

---

## Architecture

### Phase Flow (v2)

```
Phase 1  — Requirement Clarification (unchanged)
Phase 2  — SQL Generation via nl-sql (unchanged)
Phase 3  — Initial Query + Visualization (unchanged)
Phase 3.5 — Analysis Engine (NEW)
              └─ Plan → Execute loop (max 5 rounds)
                  ├─ period_compare
                  ├─ auto_drilldown
                  ├─ anomaly_detect
                  ├─ trend_forecast
                  └─ event_correlate
Phase 4  — Expert Debate (UPGRADED from parallel summary)
              └─ Round 1: Initial opinions (parallel)
              └─ Round 2: Cross-challenges (serial)
              └─ Round 3: Responses + corrections (serial)
              └─ Arbiter: convergence check → verdict
              └─ Repeat up to MAX_DEBATE_ROUNDS if not converged
Phase 5  — Feishu document publish (enhanced report structure)
```

---

## Phase 3.5: Analysis Engine

### Responsibility

After the initial query data is collected, the Analysis Engine decides what supplementary analyses are needed — without being told explicitly by the user. It generates a JSON analysis plan, executes each step using the 5 new tools, and merges all results into a unified data package for the experts.

### Analysis Plan Generation

The Orchestrator calls `generate_analysis_plan(data_summary)` which makes a single LLM call with this prompt:

```
You have the following initial query result: {data_summary}
The user's analysis goal is: {analysis_brief}

Select which analysis actions are needed from the list below.
Only include actions that would materially improve the analysis.
Output a JSON array of steps to execute.

Available actions:
1. period_compare — if YoY/WoW comparison would be meaningful
2. auto_drilldown — if there is notable variation that needs dimension attribution
3. anomaly_detect — if the data is a time series with ≥3 data points
4. trend_forecast — if the user cares about future trajectory
5. event_correlate — if anomalies are found that could be linked to events

Output format:
[
  {"action": "period_compare", "params": {"compare_type": "wow|yoy|mom"}},
  {"action": "auto_drilldown", "params": {"dimensions": ["is_new_2024", "app_launch_way"]}},
  {"action": "anomaly_detect", "params": {"metric_column": "dau", "date_column": "date"}},
  {"action": "trend_forecast", "params": {"metric_column": "dau", "forecast_days": 7}},
  {"action": "event_correlate", "params": {"anomaly_dates": ["20260418"]}}
]
```

### Execution Loop

```python
# analysis_engine.py
MAX_ANALYSIS_ROUNDS = 5

async def run_analysis_engine(initial_data: str, sql_used: str, analysis_brief: str) -> AnalysisPackage:
    package = AnalysisPackage(initial_data=initial_data, sql_used=sql_used)

    for round_num in range(MAX_ANALYSIS_ROUNDS):
        plan = await generate_analysis_plan(package.summary(), analysis_brief)
        if not plan:
            break
        for step in plan:
            result = execute_analysis_step(step, sql_used, package)
            package.merge(result)

    return package
```

`AnalysisPackage` accumulates all results and provides a `summary()` method that returns a compact representation for the next plan generation round.

---

## 5 New Analysis Tools

### 1. `period_compare` — Period-over-Period Comparison

**Input:** `sql` (original query SQL), `compare_type` (wow/yoy/mom), `current_start`, `current_end`

**Mechanism:**
1. Parse the WHERE date range from the original SQL
2. Automatically shift the date range back by 7d/28d/365d to generate comparison SQL
3. Execute both SQLs via kyuubi CLI
4. Python-layer calculation: absolute change, percentage change, direction

**Output:**
```json
{
  "current": {"total": 29928239, "avg": 4275462},
  "previous": {"total": 30154820, "avg": 4307831},
  "change_abs": -226581,
  "change_pct": -0.75,
  "direction": "down"
}
```

### 2. `auto_drilldown` — Dimension Attribution

**Input:** `sql` (original SQL), `dimensions` (list from nl-sql reference)

**Mechanism:**
1. Load available dimensions from `nl-sql/reference/{business_line}/metric-dimension-index.md`
2. For each dimension, generate a GROUP BY SQL and execute via kyuubi
3. Calculate each dimension value's contribution to the overall change
4. Rank by absolute contribution

**Output:**
```json
{
  "dimension": "app_launch_way",
  "top_contributors": [
    {"value": "第三方调起", "contribution_pct": -62.3, "abs_change": -141119},
    {"value": "点击icon",   "contribution_pct": -18.1, "abs_change": -41011}
  ]
}
```

### 3. `anomaly_detect` — Statistical Anomaly Detection

**Input:** `csv_data` (time series CSV), `metric_column`, `date_column`

**Mechanism:** Pure Python (pandas + scipy).
- Compute rolling mean and standard deviation (window=7)
- Flag points where `|value - rolling_mean| > 2σ` as anomalies
- Return severity: mild (2-3σ), moderate (3-4σ), severe (>4σ)

**Output:**
```json
{
  "anomalies": [
    {"date": "20260418", "value": 27340000, "zscore": -2.71, "severity": "moderate", "direction": "down"}
  ]
}
```

### 4. `trend_forecast` — Time Series Forecasting

**Input:** `csv_data`, `metric_column`, `date_column`, `forecast_days`

**Mechanism:** Pure Python (pandas + scipy).
- Fit linear regression on the last 14 days of data
- Project forward `forecast_days` days
- Compute 90% confidence interval from residuals

**Output:**
```json
{
  "forecast": [
    {"date": "20260422", "predicted": 30150000, "lower": 29500000, "upper": 30800000}
  ],
  "trend_direction": "flat",
  "r_squared": 0.82
}
```

### 5. `event_correlate` — Event Timeline Correlation

**Input:** `anomaly_dates` (list), reads `config/events.json`

**Mechanism:**
- For each anomaly date, look within a ±3-day window for events in `config/events.json`
- Return matched events sorted by proximity

**`config/events.json` schema:**
```json
[
  {
    "date": "20260417",
    "type": "version_release",
    "description": "浏览器 v15.6.0 发布",
    "business_line": "browser-main"
  },
  {
    "date": "20260415",
    "type": "operation",
    "description": "信息流双周活动上线",
    "business_line": "browser-feed"
  }
]
```

**Output:**
```json
{
  "correlations": [
    {
      "anomaly_date": "20260418",
      "matched_event": {"date": "20260417", "type": "version_release", "description": "浏览器 v15.6.0 发布"},
      "days_diff": 1
    }
  ]
}
```

---

## Phase 4: Expert Debate Protocol

### Round Structure

**Round 1 — Initial Opinions (parallel, same as v1)**
Each expert receives the full `AnalysisPackage` and produces their initial analysis.

**Round 2 — Cross-Challenges (serial)**
Each expert receives the other two experts' Round 1 opinions and produces:
- Specific challenges (must cite data or logic, not vague disagreement)
- Supplementary points the other missed
- Explicit support for conclusions they agree with

Prompt guidance: "You MUST either challenge or support each of the other experts' key conclusions. Vague statements like 'interesting point' are not acceptable."

**Round 3 — Responses and Corrections (serial)**
Each expert receives the challenges directed at them and produces:
- Corrections: where they now agree with the challenger
- Defenses: where they maintain their position, with added reasoning
- Explicit flag: "REVISED" or "MAINTAINED" per contested conclusion

**Arbiter Verdict**
The Arbiter receives all three rounds and outputs:
```json
{
  "converged": true,
  "consensus_conclusions": ["DAU下降主要由第三方调起减少驱动", "版本发布v15.6.0是主要归因事件"],
  "disagreements": [
    {
      "topic": "季节性影响程度",
      "positions": {
        "SQL工程师": "季节性因素占比约20%",
        "数据分析师": "季节性因素不显著，主要是版本问题"
      }
    }
  ],
  "final_recommendation": "优先回查 v15.6.0 发布后第三方调起链路是否有变更...",
  "confidence": "high"
}
```

If `converged = false` and `debate_round < MAX_DEBATE_ROUNDS (3)`, extract the disagreement points and start a new debate round focused on those specific topics.

### Token Budget

| Step | API calls | Approx tokens |
|------|-----------|---------------|
| Round 1 (parallel ×3) | 3 | ~12k |
| Round 2 (serial ×3) | 3 | ~9k |
| Round 3 (serial ×3) | 3 | ~9k |
| Arbiter | 1 | ~6k |
| Per additional round | +7 | +~24k |
| **Max (3 debate rounds)** | **~24** | **~80k** |

---

## Enhanced Feishu Report Structure

```markdown
# {指标} 深度分析报告
> 分析时间 | 业务线 | 周期 | 分析引擎执行了 N 个补充查询 | 辩论 N 轮收敛

## 摘要
（仲裁者最终结论，3-5 句话）

## 数据概览与对比
| 指标 | 本期 | 上期(环比) | 上期(同比) | 环比变化 | 同比变化 |

## 异常检测
（标记异常日期、偏离程度、方向）

## 异常归因
（贡献维度排名，柱状图）

## 事件关联
（与异常匹配的版本发布/运营活动时间线）

## 趋势预测
（未来 N 天预测值 + 置信区间折线图）

## 专家共识
（三方一致同意的核心结论）

## 专家分歧（已记录，供参考）
（分歧主题 + 各方立场）

## 行动建议
（仲裁者综合建议，按优先级排序）

## 附录
- 初始 SQL + 分析引擎补充 SQL 列表
- 辩论轮次摘要
```

---

## File Structure Changes

```
data_analysis/
├── agent.py                        # Modified: add Phase 3.5 engine call
├── config.py                       # Modified: MAX_ANALYSIS_ROUNDS=5, MAX_DEBATE_ROUNDS=3
├── config/
│   └── events.json                 # NEW: event calendar
├── tools/
│   ├── (existing 6 tools unchanged)
│   ├── period_compare.py           # NEW
│   ├── auto_drilldown.py           # NEW
│   ├── anomaly_detect.py           # NEW (pandas + scipy)
│   ├── trend_forecast.py           # NEW (pandas + scipy)
│   └── event_correlate.py          # NEW
├── experts/
│   ├── prompts.py                  # Modified: add CHALLENGE/RESPONSE/ARBITER prompts
│   ├── runner.py                   # Modified: run_debate() multi-round loop
│   └── analysis_engine.py          # NEW: plan generation + execution loop
└── requirements.txt                # Modified: add scipy
```

---

## Configuration

```python
# config.py additions
MAX_ANALYSIS_ROUNDS = 5    # max iterations of the analysis engine
MAX_DEBATE_ROUNDS = 3      # max rounds before arbiter forces a verdict
ANOMALY_THRESHOLD_SIGMA = 2.0
FORECAST_DAYS_DEFAULT = 7
EVENT_CORRELATE_WINDOW_DAYS = 3
```

---

## Constraints

1. **Analysis Engine never writes SQL directly.** It passes parameters to tools which derive SQL from the original nl-sql-generated query. All SQL still originates from nl-sql reference data.
2. **Debate rounds are capped.** After `MAX_DEBATE_ROUNDS`, the Arbiter issues a verdict regardless of convergence, marking remaining disagreements explicitly.
3. **Analysis Engine rounds are capped.** After `MAX_ANALYSIS_ROUNDS`, remaining plan steps are skipped and a warning is noted in the report.
4. **event_correlate is best-effort.** If `config/events.json` has no entry near an anomaly date, the section is omitted from the report rather than fabricating correlations.
5. **Backward compatible.** If the user says "skip deep analysis" or "quick mode", Phase 3.5 is bypassed and v1 behavior is used.
