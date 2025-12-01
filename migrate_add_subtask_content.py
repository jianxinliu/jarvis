#!/usr/bin/env python3
"""数据库迁移脚本：为 todo_sub_tasks 表添加 content 字段."""

import sqlite3
import sys
from pathlib import Path

# 获取数据库路径
db_path = Path("jarvis.db")
if not db_path.exists():
    print("错误：找不到数据库文件 jarvis.db")
    sys.exit(1)

print(f"正在迁移数据库: {db_path}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 为 todo_sub_tasks 表添加 content 字段
    print("检查 todo_sub_tasks 表的 content 字段...")
    cursor.execute("PRAGMA table_info(todo_sub_tasks)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "content" in columns:
        print("字段 content 已存在，跳过添加")
    else:
        print("正在添加 content 字段...")
        cursor.execute("""
            ALTER TABLE todo_sub_tasks 
            ADD COLUMN content TEXT
        """)
        print("✓ 已添加 content 字段")
    
    conn.commit()
    print("\n迁移成功！")
    print("- 已更新 todo_sub_tasks 表（添加 content 字段）")
    
    conn.close()
    
except Exception as e:
    print(f"\n迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

