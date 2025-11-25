#!/usr/bin/env python3
"""数据库迁移脚本：为 TODO 应用添加子任务功能和间隔提醒字段."""

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
    
    # 1. 为 todo_items 表添加 reminder_interval_hours 字段
    print("检查 todo_items 表的 reminder_interval_hours 字段...")
    cursor.execute("PRAGMA table_info(todo_items)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "reminder_interval_hours" in columns:
        print("字段 reminder_interval_hours 已存在，跳过添加")
    else:
        print("正在添加 reminder_interval_hours 字段...")
        cursor.execute("""
            ALTER TABLE todo_items 
            ADD COLUMN reminder_interval_hours INTEGER
        """)
        print("✓ 已添加 reminder_interval_hours 字段")
    
    # 2. 为 todo_items 表添加 next_reminder_time 字段
    print("检查 todo_items 表的 next_reminder_time 字段...")
    if "next_reminder_time" in columns:
        print("字段 next_reminder_time 已存在，跳过添加")
    else:
        print("正在添加 next_reminder_time 字段...")
        cursor.execute("""
            ALTER TABLE todo_items 
            ADD COLUMN next_reminder_time DATETIME
        """)
        print("✓ 已添加 next_reminder_time 字段")
    
    # 3. 创建 todo_sub_tasks 表
    print("检查 todo_sub_tasks 表...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='todo_sub_tasks'
    """)
    if cursor.fetchone():
        print("表 todo_sub_tasks 已存在，跳过创建")
    else:
        print("正在创建 todo_sub_tasks 表...")
        cursor.execute("""
            CREATE TABLE todo_sub_tasks (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                todo_item_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                reminder_time DATETIME NOT NULL,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                is_notified BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(todo_item_id) REFERENCES todo_items (id) ON DELETE CASCADE
            )
        """)
        # 创建索引
        cursor.execute("CREATE INDEX ix_todo_sub_tasks_id ON todo_sub_tasks (id)")
        cursor.execute("CREATE INDEX ix_todo_sub_tasks_todo_item_id ON todo_sub_tasks (todo_item_id)")
        print("✓ 已创建 todo_sub_tasks 表")
    
    conn.commit()
    print("\n迁移成功！")
    print("- 已更新 todo_items 表（添加 reminder_interval_hours 和 next_reminder_time 字段）")
    print("- 已创建 todo_sub_tasks 表")
    
    conn.close()
    
except Exception as e:
    print(f"\n迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

