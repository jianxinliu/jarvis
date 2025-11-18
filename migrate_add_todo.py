#!/usr/bin/env python3
"""数据库迁移脚本：添加 TODO 应用相关表."""

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
    
    # 1. 创建 todo_items 表
    print("检查 todo_items 表...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='todo_items'
    """)
    if cursor.fetchone():
        print("表 todo_items 已存在，跳过创建")
    else:
        print("正在创建 todo_items 表...")
        cursor.execute("""
            CREATE TABLE todo_items (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                content TEXT,
                quadrant VARCHAR(20) NOT NULL,
                priority_id INTEGER,
                due_time DATETIME,
                reminder_time DATETIME,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                is_archived BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY(priority_id) REFERENCES todo_priorities (id)
            )
        """)
        cursor.execute("CREATE INDEX ix_todo_items_id ON todo_items (id)")
        cursor.execute("CREATE INDEX ix_todo_items_quadrant ON todo_items (quadrant)")
        cursor.execute("CREATE INDEX ix_todo_items_priority_id ON todo_items (priority_id)")
        print("✓ 已创建 todo_items 表")
    
    # 2. 创建 todo_tags 表
    print("检查 todo_tags 表...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='todo_tags'
    """)
    if cursor.fetchone():
        print("表 todo_tags 已存在，跳过创建")
    else:
        print("正在创建 todo_tags 表...")
        cursor.execute("""
            CREATE TABLE todo_tags (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                color VARCHAR(20),
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
        """)
        cursor.execute("CREATE INDEX ix_todo_tags_id ON todo_tags (id)")
        cursor.execute("CREATE INDEX ix_todo_tags_name ON todo_tags (name)")
        print("✓ 已创建 todo_tags 表")
    
    # 3. 创建 todo_priorities 表
    print("检查 todo_priorities 表...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='todo_priorities'
    """)
    if cursor.fetchone():
        print("表 todo_priorities 已存在，跳过创建")
    else:
        print("正在创建 todo_priorities 表...")
        cursor.execute("""
            CREATE TABLE todo_priorities (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                level INTEGER NOT NULL,
                color VARCHAR(20),
                created_at DATETIME NOT NULL DEFAULT (datetime('now')),
                updated_at DATETIME NOT NULL DEFAULT (datetime('now'))
            )
        """)
        cursor.execute("CREATE INDEX ix_todo_priorities_id ON todo_priorities (id)")
        cursor.execute("CREATE INDEX ix_todo_priorities_level ON todo_priorities (level)")
        print("✓ 已创建 todo_priorities 表")
        
        # 创建默认优先级
        print("正在创建默认优先级...")
        default_priorities = [
            ("最高", 1, "#f44336"),
            ("高", 2, "#ff9800"),
            ("中", 3, "#2196f3"),
            ("低", 4, "#4caf50"),
            ("最低", 5, "#9e9e9e"),
        ]
        for name, level, color in default_priorities:
            cursor.execute("""
                INSERT INTO todo_priorities (name, level, color)
                VALUES (?, ?, ?)
            """, (name, level, color))
        print("✓ 已创建默认优先级")
    
    # 4. 创建 todo_item_tag 关联表
    print("检查 todo_item_tag 表...")
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='todo_item_tag'
    """)
    if cursor.fetchone():
        print("表 todo_item_tag 已存在，跳过创建")
    else:
        print("正在创建 todo_item_tag 表...")
        cursor.execute("""
            CREATE TABLE todo_item_tag (
                todo_item_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (todo_item_id, tag_id),
                FOREIGN KEY(todo_item_id) REFERENCES todo_items (id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES todo_tags (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX ix_todo_item_tag_todo_item_id ON todo_item_tag (todo_item_id)")
        cursor.execute("CREATE INDEX ix_todo_item_tag_tag_id ON todo_item_tag (tag_id)")
        print("✓ 已创建 todo_item_tag 表")
    
    conn.commit()
    print("\n迁移成功！")
    print("- 已创建 todo_items 表")
    print("- 已创建 todo_tags 表")
    print("- 已创建 todo_priorities 表（包含默认优先级）")
    print("- 已创建 todo_item_tag 关联表")
    
    conn.close()
    
except Exception as e:
    print(f"\n迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

