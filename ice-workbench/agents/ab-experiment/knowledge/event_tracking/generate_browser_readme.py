#!/usr/bin/env python3
"""生成浏览器埋点知识库的可读Markdown文档"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'browser_event_tracking.db')
MD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'browser_event_tracking_readme.md')


def generate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    lines = []
    lines.append('# 浏览器埋点事件知识库')
    lines.append('')

    # Metadata
    lines.append('## 基本信息')
    lines.append('')
    for row in c.execute("SELECT key, value FROM metadata ORDER BY key"):
        lines.append(f'- **{row[0]}**: {row[1]}')
    lines.append('')

    # Stats overview
    lines.append('## 数据概览')
    lines.append('')
    stats = {
        'categories': c.execute('SELECT COUNT(*) FROM categories').fetchone()[0],
        'sdk_fields': c.execute('SELECT COUNT(*) FROM sdk_fields').fetchone()[0],
        'common_field_groups': c.execute('SELECT COUNT(*) FROM common_field_groups').fetchone()[0],
        'common_fields': c.execute('SELECT COUNT(*) FROM common_fields').fetchone()[0],
        'pages': c.execute('SELECT COUNT(*) FROM pages').fetchone()[0],
        'events': c.execute('SELECT COUNT(*) FROM events').fetchone()[0],
        'event_fields': c.execute('SELECT COUNT(*) FROM event_fields').fetchone()[0],
        'event_common_field_refs': c.execute('SELECT COUNT(*) FROM event_common_field_refs').fetchone()[0],
        'event_page_refs': c.execute('SELECT COUNT(*) FROM event_page_refs').fetchone()[0],
        'event_metric_refs': c.execute('SELECT COUNT(*) FROM event_metric_refs').fetchone()[0],
    }
    lines.append('| 项目 | 数量 |')
    lines.append('|------|------|')
    for k, v in stats.items():
        lines.append(f'| {k} | {v} |')
    lines.append('')

    # Category breakdown
    lines.append('### 事件分类统计')
    lines.append('')
    lines.append('| 分类 | 中文名 | 事件数 | 说明 |')
    lines.append('|------|--------|--------|------|')
    for row in c.execute("""
        SELECT c.name, c.name_cn, COUNT(e.id), c.description
        FROM categories c
        LEFT JOIN events e ON c.name=e.category
        GROUP BY c.name
        ORDER BY COUNT(e.id) DESC
    """):
        lines.append(f'| {row[0]} | {row[1]} | {row[2]} | {row[3]} |')
    lines.append('')

    # Experiment ID fields
    lines.append('### 实验ID字段')
    lines.append('')
    lines.append('| 字段名 | 中文名 | 类型 | 说明 |')
    lines.append('|--------|--------|------|------|')
    for row in c.execute("SELECT name, name_cn, type, value_note FROM common_fields WHERE name IN ('eid', 'exp_id', 'new_eid')"):
        lines.append(f'| {row[0]} | {row[1]} | {row[2]} | {row[3][:80] if row[3] else ""} |')
    lines.append('')

    # Metric-Event mapping
    lines.append('### 核心指标 ↔ 事件映射')
    lines.append('')
    lines.append('| 指标 | 关联事件 |')
    lines.append('|------|----------|')
    for row in c.execute("""
        SELECT m.metric_name, GROUP_CONCAT(e.name, ', ')
        FROM event_metric_refs m
        JOIN events e ON m.event_id=e.id
        GROUP BY m.metric_name
    """):
        lines.append(f'| {row[0]} | {row[1]} |')
    lines.append('')

    # Page-Event mapping (top pages)
    lines.append('### 页面 ↔ 事件映射（Top 15）')
    lines.append('')
    lines.append('| 页面 | 中文名 | 关联事件数 |')
    lines.append('|------|--------|------------|')
    for row in c.execute("""
        SELECT p.page_key, p.name_cn, COUNT(r.id)
        FROM pages p
        JOIN event_page_refs r ON p.id=r.page_id
        GROUP BY p.id
        ORDER BY COUNT(r.id) DESC
        LIMIT 15
    """):
        lines.append(f'| {row[0]} | {row[1]} | {row[2]} |')
    lines.append('')

    # SDK fields
    lines.append('## OneTrack SDK系统属性')
    lines.append('')
    lines.append('| 属性名 | 中文名 | 类型 | 说明 |')
    lines.append('|--------|--------|------|------|')
    for row in c.execute("SELECT name, name_cn, type, description FROM sdk_fields ORDER BY id"):
        lines.append(f'| {row[0]} | {row[1]} | {row[2]} | {row[3][:60] if row[3] else ""} |')
    lines.append('')

    # Common field groups
    lines.append('## 公共字段组')
    lines.append('')
    for group in c.execute("SELECT id, name, name_cn, description, scope FROM common_field_groups ORDER BY sort_order"):
        lines.append(f'### {group[1]} ({group[2]})')
        lines.append(f'- 说明: {group[3]}')
        lines.append(f'- 作用域: {group[4]}')
        lines.append('')
        lines.append('| 字段名 | 中文名 | 类型 | 说明 | 值说明 | 版本 |')
        lines.append('|--------|--------|------|------|--------|------|')
        for field in c.execute("SELECT name, name_cn, type, description, value_note, app_ver FROM common_fields WHERE group_id=? ORDER BY id", (group[0],)):
            desc = (field[3] or '')[:50]
            vn = (field[4] or '')[:60]
            lines.append(f'| {field[0]} | {field[1]} | {field[2]} | {desc} | {vn} | {field[5] or ""} |')
        lines.append('')

    # Pages
    lines.append('## 页面定义')
    lines.append('')
    lines.append('| 页面key | 中文名 | 分类 | 模块key | 模块中文名 | 备注 |')
    lines.append('|---------|--------|------|---------|------------|------|')
    for row in c.execute("SELECT page_key, name_cn, category, module_key, module_cn, note FROM pages ORDER BY id"):
        lines.append(f'| {row[0]} | {row[1]} | {row[2][:30] if row[2] else ""} | {row[3] or ""} | {row[4] or ""} | {(row[5] or "")[:40]} |')
    lines.append('')

    # Events by category
    lines.append('## 事件详情（按分类）')
    lines.append('')
    for cat in c.execute("SELECT name, name_cn, description FROM categories ORDER BY sort_order"):
        cat_name, cat_cn, cat_desc = cat
        events = c.execute("SELECT id, name, name_cn, report_when, note, incognito_report, app_ver FROM events WHERE category=? ORDER BY id", (cat_name,)).fetchall()
        if not events:
            continue

        lines.append(f'### {cat_name} - {cat_cn}')
        if cat_desc:
            lines.append(f'*{cat_desc}*')
        lines.append('')

        for ev in events:
            ev_id, ev_name, ev_cn, report, note, incognito, app_ver = ev
            lines.append(f'#### {ev_name} ({ev_cn})')
            if report:
                lines.append(f'- **上报时机**: {report[:200]}')
            if note:
                lines.append(f'- **备注**: {note[:200]}')
            if incognito:
                lines.append(f'- **无痕模式上报**: {incognito}')
            if app_ver:
                lines.append(f'- **版本**: {app_ver}')

            # Common field refs
            refs = c.execute("""
                SELECT g.name, g.name_cn FROM event_common_field_refs r
                JOIN common_field_groups g ON r.group_id=g.id
                WHERE r.event_id=?
            """, (ev_id,)).fetchall()
            if refs:
                ref_str = ', '.join([f'{r[0]}({r[1]})' for r in refs])
                lines.append(f'- **公共属性引用**: {ref_str}')

            # Page refs
            pages = c.execute("""
                SELECT p.page_key, p.name_cn FROM event_page_refs r
                JOIN pages p ON r.page_id=p.id
                WHERE r.event_id=?
            """, (ev_id,)).fetchall()
            if pages:
                page_str = ', '.join([f'{p[0]}({p[1]})' for p in pages])
                lines.append(f'- **关联页面**: {page_str}')

            # Metric refs
            metrics = c.execute("""
                SELECT metric_name FROM event_metric_refs
                WHERE event_id=?
            """, (ev_id,)).fetchall()
            if metrics:
                metric_str = ', '.join([m[0] for m in metrics])
                lines.append(f'- **关联指标**: {metric_str}')

            # Fields
            fields = c.execute("SELECT name, name_cn, type, value_note, description FROM event_fields WHERE event_id=? ORDER BY sort_order", (ev_id,)).fetchall()
            if fields:
                lines.append('')
                lines.append('| 字段名 | 中文名 | 类型 | 值说明 | 备注 |')
                lines.append('|--------|--------|------|--------|------|')
                for f in fields:
                    vn = (f[3] or '')[:80]
                    desc = (f[4] or '')[:60]
                    lines.append(f'| {f[0]} | {f[1]} | {f[2]} | {vn} | {desc} |')

            lines.append('')

    # Query examples
    lines.append('## 常用查询示例')
    lines.append('')
    lines.append('```sql')
    lines.append("-- 1. 按指标查关联事件")
    lines.append("SELECT e.name, e.name_cn FROM events e")
    lines.append("JOIN event_metric_refs m ON e.id=m.event_id")
    lines.append("WHERE m.metric_name='浏览器信息流人均时长';")
    lines.append('')
    lines.append("-- 2. 按页面查关联事件")
    lines.append("SELECT e.name, e.name_cn FROM events e")
    lines.append("JOIN event_page_refs r ON e.id=r.event_id")
    lines.append("JOIN pages p ON r.page_id=p.id")
    lines.append("WHERE p.page_key='feed_info_topnews';")
    lines.append('')
    lines.append("-- 3. 按分类查所有事件")
    lines.append("SELECT name, name_cn FROM events WHERE category='content';")
    lines.append('')
    lines.append("-- 4. 查事件的完整信息（字段+公共属性+页面+指标）")
    lines.append("SELECT * FROM event_fields WHERE event_id=(SELECT id FROM events WHERE name='content_item_expose');")
    lines.append("SELECT g.name FROM event_common_field_refs r JOIN common_field_groups g ON r.group_id=g.id WHERE r.event_id=(SELECT id FROM events WHERE name='content_item_expose');")
    lines.append("SELECT p.page_key FROM event_page_refs r JOIN pages p ON r.page_id=p.id WHERE r.event_id=(SELECT id FROM events WHERE name='content_item_expose');")
    lines.append("SELECT metric_name FROM event_metric_refs WHERE event_id=(SELECT id FROM events WHERE name='content_item_expose');")
    lines.append('')
    lines.append("-- 5. 查实验ID字段")
    lines.append("SELECT name, name_cn, type, value_note FROM common_fields WHERE name IN ('eid', 'exp_id');")
    lines.append('')
    lines.append("-- 6. 查页面定义")
    lines.append("SELECT page_key, name_cn, category FROM pages WHERE category LIKE '%信息流%';")
    lines.append('```')
    lines.append('')

    content = '\n'.join(lines)
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f'生成完成: {MD_PATH}')
    print(f'文件大小: {len(content)} 字符, {len(lines)} 行')

    conn.close()


if __name__ == '__main__':
    generate()
