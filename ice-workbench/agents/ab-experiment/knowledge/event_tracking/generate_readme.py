#!/usr/bin/env python3
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "event_tracking.db")
MD_PATH = os.path.join(os.path.dirname(__file__), "event_tracking_readme.md")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

lines = []
lines.append("# 埋点事件知识库 - 数据摘要")
lines.append("")
lines.append(f"> 数据源: `event_tracking.db` (SQLite) | 生成脚本: `generate_readme.py`")
lines.append("")

lines.append("## 总览")
lines.append("")
cur.execute("SELECT COUNT(*) FROM events")
total_events = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM event_fields")
total_fields = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM common_fields")
total_common = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM event_relations WHERE relation_type='metric'")
total_metric_relations = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM event_relations WHERE relation_type='page'")
total_page_relations = cur.fetchone()[0]
lines.append(f"| 维度 | 数量 |")
lines.append(f"|------|------|")
lines.append(f"| 事件总数 | {total_events} |")
lines.append(f"| 事件特有字段 | {total_fields} |")
lines.append(f"| 公共字段 | {total_common} |")
lines.append(f"| 指标关联 | {total_metric_relations} |")
lines.append(f"| 页面关联 | {total_page_relations} |")
lines.append("")

lines.append("## 事件分类")
lines.append("")
lines.append("| 分类 | 数量 | 说明 |")
lines.append("|------|------|------|")
category_desc = {
    "content": "内容相关（曝光/点击/浏览/播放/互动）",
    "app": "app通用（打开/退出/弹窗/引导）",
    "search": "搜索相关",
    "operation": "运营位",
    "ad": "广告",
    "livestream": "直播间",
    "skit": "短剧",
    "incentive": "激励体系",
    "exception": "异常事件",
    "me": "我的页面",
    "tab": "tab标签",
    "growth": "拉新拉活",
}
cur.execute("SELECT category, COUNT(*) FROM events GROUP BY category ORDER BY COUNT(*) DESC")
for row in cur.fetchall():
    lines.append(f"| {row[0]} | {row[1]} | {category_desc.get(row[0], '')} |")
lines.append("")

lines.append("## 核心指标 <-> 事件映射")
lines.append("")
lines.append("| 核心指标 | 关联事件 |")
lines.append("|----------|---------|")
cur.execute("""
    SELECT r.relation_name, GROUP_CONCAT(e.name, ', ')
    FROM event_relations r
    JOIN events e ON r.event_id=e.id
    WHERE r.relation_type='metric'
    GROUP BY r.relation_name
    ORDER BY r.relation_name
""")
for row in cur.fetchall():
    lines.append(f"| {row[0]} | {row[1]} |")
lines.append("")

lines.append("## 实验ID字段")
lines.append("")
lines.append("| 字段名 | 类型 | 说明 | 位置 |")
lines.append("|--------|------|------|------|")
lines.append("| eid | string | 旧实验id | 公共参数（所有事件携带） |")
lines.append("| new_eid | string | 新实验id（服务端下发） | 公共参数（所有事件携带） |")
lines.append("| ad_exp_id | string | 广告实验id | 广告事件特有字段 |")
lines.append("")

lines.append("## 事件详情（按分类）")
lines.append("")
cur.execute("SELECT id, name, name_cn, category, report_when FROM events ORDER BY category, id")
current_category = None
for ev in cur.fetchall():
    eid, ename, cn, cat, report_when = ev
    if cat != current_category:
        current_category = cat
        lines.append(f"### {cat} ({category_desc.get(cat, '')})")
        lines.append("")

    lines.append(f"#### `{ename}` — {cn}")
    lines.append("")

    if report_when:
        rw = report_when.replace("\n", " ")[:200]
        lines.append(f"**上报时机**: {rw}")
        lines.append("")

    cur.execute("SELECT name, name_cn, type, description FROM event_fields WHERE event_id=? ORDER BY sort_order, id", (eid,))
    fields = cur.fetchall()
    if fields:
        lines.append("| 字段名 | 中文名 | 类型 | 说明 |")
        lines.append("|--------|--------|------|------|")
        for f in fields:
            desc = (f[3] or "").replace("\n", " ")[:100]
            lines.append(f"| {f[0]} | {f[1] or ''} | {f[2]} | {desc} |")
        lines.append("")

    cur.execute("SELECT relation_type, relation_name FROM event_relations WHERE event_id=?", (eid,))
    rels = cur.fetchall()
    if rels:
        metrics = [r[1] for r in rels if r[0] == "metric"]
        pages = [r[1] for r in rels if r[0] == "page"]
        if metrics:
            lines.append(f"**关联指标**: {', '.join(metrics)}")
        if pages:
            lines.append(f"**关联页面**: {', '.join(pages)}")
        lines.append("")

    cur.execute("""
        SELECT cfg.name FROM event_common_field_refs ecr
        JOIN common_field_groups cfg ON ecr.group_id=cfg.id
        WHERE ecr.event_id=?
    """, (eid,))
    groups = [g[0] for g in cur.fetchall()]
    if groups:
        lines.append(f"**引用公共字段组**: {', '.join(groups)}")
        lines.append("")

lines.append("---")
lines.append("")
lines.append("## 公共字段定义")
lines.append("")

cur.execute("SELECT id, name, description FROM common_field_groups ORDER BY id")
for grp in cur.fetchall():
    gid, gname, gdesc = grp
    lines.append(f"### {gname}")
    if gdesc:
        lines.append(f"{gdesc}")
    lines.append("")
    lines.append("| 字段名 | 中文名 | 类型 | 说明 |")
    lines.append("|--------|--------|------|------|")
    cur.execute("SELECT name, name_cn, type, description, value_note FROM common_fields WHERE group_id=? ORDER BY id", (gid,))
    for cf in cur.fetchall():
        desc = (cf[3] or "").replace("\n", " ")[:80]
        if cf[4]:
            desc += f" ({cf[4].replace(chr(10), ' ')[:50]})"
        lines.append(f"| {cf[0]} | {cf[1] or ''} | {cf[2]} | {desc} |")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("*此文件由 `generate_readme.py` 从 `event_tracking.db` 自动生成，如需更新请重新运行脚本*")

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Generated: {MD_PATH}")
print(f"Lines: {len(lines)}")
conn.close()
