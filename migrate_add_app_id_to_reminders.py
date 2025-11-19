#!/usr/bin/env python3
"""数据库迁移脚本：为 reminder_logs 表添加 app_id 字段."""

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
    
    # 检查 app_id 字段是否已存在
    print("检查 reminder_logs 表的 app_id 字段...")
    cursor.execute("PRAGMA table_info(reminder_logs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "app_id" in columns:
        print("字段 app_id 已存在，跳过添加")
    else:
        print("正在添加 app_id 字段...")
        cursor.execute("""
            ALTER TABLE reminder_logs 
            ADD COLUMN app_id VARCHAR(100)
        """)
        print("✓ 已添加 app_id 字段")
        
        # 创建索引
        print("正在创建索引...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS ix_reminder_logs_app_id 
            ON reminder_logs (app_id)
        """)
        print("✓ 已创建索引")
        
        # 根据现有数据更新 app_id（可选，用于历史数据）
        print("正在更新历史数据的 app_id...")
        cursor.execute("""
            UPDATE reminder_logs 
            SET app_id = 'tasks' 
            WHERE reminder_type IN ('interval', 'daily', 'subtask') 
            AND app_id IS NULL
        """)
        tasks_count = cursor.rowcount
        
        cursor.execute("""
            UPDATE reminder_logs 
            SET app_id = 'todo' 
            WHERE reminder_type IN ('todo', 'todo_daily') 
            AND app_id IS NULL
        """)
        todo_count = cursor.rowcount
        
        print(f"✓ 已更新 {tasks_count + todo_count} 条历史记录的 app_id")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(reminder_logs)")
        columns_after = [row[1] for row in cursor.fetchall()]
        if "app_id" in columns_after:
            print("✓ 验证成功：app_id 字段已添加到 reminder_logs 表")
        else:
            print("⚠ 警告：无法验证字段是否添加成功")
    
    conn.commit()
    print("\n迁移成功！")
    print("- 已为 reminder_logs 表添加 app_id 字段")
    print("- 已创建索引")
    print("- 已更新历史数据")
    print("- 说明：此字段用于标识提醒来自哪个应用")
    
    conn.close()
    
except Exception as e:
    print(f"\n迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

