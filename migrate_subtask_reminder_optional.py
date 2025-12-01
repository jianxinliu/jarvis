#!/usr/bin/env python3
"""数据库迁移脚本：将 todo_sub_tasks 表的 reminder_time 字段改为可选."""

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
    
    # SQLite 不支持直接修改列的 nullable 属性
    # 需要重建表
    print("检查 todo_sub_tasks 表结构...")
    cursor.execute("PRAGMA table_info(todo_sub_tasks)")
    columns = cursor.fetchall()
    
    # 检查 reminder_time 是否已经是可选的（在 SQLite 中，NULL 值总是允许的，但我们需要确保约束正确）
    # SQLite 的 ALTER TABLE 限制较多，我们需要检查是否有 NOT NULL 约束
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='todo_sub_tasks'")
    table_sql = cursor.fetchone()
    
    if table_sql and 'reminder_time DATETIME NOT NULL' in table_sql[0]:
        print("需要修改 reminder_time 字段为可选...")
        print("SQLite 不支持直接修改列的约束，但 NULL 值在 SQLite 中总是允许的")
        print("如果 reminder_time 有 NOT NULL 约束，需要重建表...")
        
        # 创建新表
        print("正在创建新表...")
        cursor.execute("""
            CREATE TABLE todo_sub_tasks_new (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                todo_item_id INTEGER NOT NULL,
                title VARCHAR(200) NOT NULL,
                content TEXT,
                reminder_time DATETIME,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                is_notified BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(todo_item_id) REFERENCES todo_items (id) ON DELETE CASCADE
            )
        """)
        
        # 复制数据
        print("正在复制数据...")
        cursor.execute("""
            INSERT INTO todo_sub_tasks_new 
            (id, todo_item_id, title, content, reminder_time, is_completed, is_notified, created_at, updated_at)
            SELECT id, todo_item_id, title, content, reminder_time, is_completed, is_notified, created_at, updated_at
            FROM todo_sub_tasks
        """)
        
        # 删除旧表
        print("正在删除旧表...")
        cursor.execute("DROP TABLE todo_sub_tasks")
        
        # 重命名新表
        print("正在重命名新表...")
        cursor.execute("ALTER TABLE todo_sub_tasks_new RENAME TO todo_sub_tasks")
        
        # 重建索引
        print("正在重建索引...")
        cursor.execute("CREATE INDEX ix_todo_sub_tasks_id ON todo_sub_tasks (id)")
        cursor.execute("CREATE INDEX ix_todo_sub_tasks_todo_item_id ON todo_sub_tasks (todo_item_id)")
        
        print("✓ 已更新 reminder_time 字段为可选")
    else:
        print("reminder_time 字段已经是可选的，跳过修改")
    
    conn.commit()
    print("\n迁移成功！")
    print("- 已更新 todo_sub_tasks 表（reminder_time 字段现在为可选）")
    
    conn.close()
    
except Exception as e:
    print(f"\n迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

