#!/usr/bin/env python3
"""
nl-sql.py — 将生成的 SQL 保存为带时间戳的文件

用法:
  python scripts/nl-sql.py --metric "<指标名称>" --sql "<SQL内容>"
  python scripts/nl-sql.py --metric "<指标名称>" --sql "<SQL内容>" --output-dir "~/Desktop/custom_dir"
  python scripts/nl-sql.py --metric "<指标名称>" --sql-file /tmp/query.sql
  cat query.sql | python scripts/nl-sql.py --metric "<指标名称>"
"""

import argparse
import sys
import os
from datetime import datetime
from pathlib import Path


def get_default_output_dir(metric_name: str) -> str:
    """生成默认的输出目录：桌面/时间戳_指标名"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    safe_metric = "".join(c for c in metric_name if c.isalnum() or c in ("-", "_", "·", "（", "）")).strip()
    if not safe_metric:
        safe_metric = "query"
    
    dir_name = f"{timestamp}_{safe_metric}"
    desktop_path = Path.home() / "Desktop"
    
    if not desktop_path.exists():
        desktop_path = Path.home()
    
    output_dir = desktop_path / dir_name
    return str(output_dir)


def main():
    parser = argparse.ArgumentParser(description="保存 SQL 文件到桌面目录")
    parser.add_argument("--metric", required=True, help="指标名称（用于文件命名）")
    parser.add_argument("--sql", help="SQL 内容字符串")
    parser.add_argument("--sql-file", help="从文件读取 SQL 内容")
    parser.add_argument("--output-dir", help="输出目录（默认：桌面/时间戳_指标名）")
    parser.add_argument("--filename", help="自定义文件名（默认：指标名称.sql）")
    args = parser.parse_args()

    # 获取 SQL 内容
    if args.sql:
        sql_content = args.sql
    elif args.sql_file:
        with open(args.sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
    elif not sys.stdin.isatty():
        sql_content = sys.stdin.read()
    else:
        print("错误：请通过 --sql、--sql-file 或 stdin 提供 SQL 内容", file=sys.stderr)
        sys.exit(1)

    # 确定输出目录
    if args.output_dir:
        output_dir = args.output_dir
        output_dir = output_dir.replace("~", str(Path.home()))
    else:
        output_dir = get_default_output_dir(args.metric)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 确定文件名
    if args.filename:
        filename = args.filename
        if not filename.endswith(".sql"):
            filename += ".sql"
    else:
        safe_metric = "".join(c for c in args.metric if c.isalnum() or c in ("-", "_", "·", "（", "）")).strip()
        if not safe_metric:
            safe_metric = "query"
        filename = f"{safe_metric}.sql"

    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(sql_content.strip())
        f.write("\n")

    print(f"✅ SQL 已保存")
    print(f"   目录：{os.path.abspath(output_dir)}")
    print(f"   文件：{os.path.abspath(filepath)}")
    return filepath


if __name__ == "__main__":
    main()
