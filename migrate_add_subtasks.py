#!/usr/bin/env python3
"""数据库迁移脚本：添加子任务功能和更新提醒记录表."""

import sqlite3
import sys
from pathlib import Path

# 获取数据库路径
db_path = Path("jarvis.db")
if not db_path.exists():
    # 尝试从环境变量或配置中获取
    print("错误：找不到数据库文件 jarvis.db")
    sys.exit(1)

print(f"正在迁移数据库: {db_path}")

try:
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # 1. 创建 sub_tasks 表（如果不存在）
    print("检查 sub_tasks 表...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='sub_tasks'
    """)
    if cursor.fetchone():
        print("表 sub_tasks 已存在，跳过创建")
    else:
        print("正在创建 sub_tasks 表...")
        cursor.execute("""
            CREATE TABLE sub_tasks (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                reminder_time DATETIME NOT NULL,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                is_notified BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
        """)
        # 创建索引
        cursor.execute("CREATE INDEX ix_sub_tasks_task_id ON sub_tasks (task_id)")
        print("✓ 已创建 sub_tasks 表")
    
    # 2. 为 reminder_logs 表添加 subtask_id 列（如果不存在）
    print("检查 reminder_logs 表的 subtask_id 字段...")
    cursor.execute("PRAGMA table_info(reminder_logs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "subtask_id" in columns:
        print("字段 subtask_id 已存在，跳过添加")
    else:
        print("正在添加 subtask_id 字段...")
        cursor.execute("""
            ALTER TABLE reminder_logs 
            ADD COLUMN subtask_id INTEGER
        """)
        # 创建索引
        cursor.execute("CREATE INDEX ix_reminder_logs_subtask_id ON reminder_logs (subtask_id)")
        print("✓ 已添加 subtask_id 字段")
    
    conn.commit()
    print("\n迁移成功！")
    print("- 已创建 sub_tasks 表")
    print("- 已更新 reminder_logs 表（添加 subtask_id 字段）")
    
    conn.close()
    
except Exception as e:
    print(f"\n迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

