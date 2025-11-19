#!/usr/bin/env python3
"""数据库迁移脚本：为 tasks 表添加 is_completed 字段."""

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
    
    # 检查 is_completed 字段是否已存在
    print("检查 tasks 表的 is_completed 字段...")
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "is_completed" in columns:
        print("字段 is_completed 已存在，跳过添加")
    else:
        print("正在添加 is_completed 字段...")
        cursor.execute("""
            ALTER TABLE tasks 
            ADD COLUMN is_completed INTEGER NOT NULL DEFAULT 0
        """)
        print("✓ 已添加 is_completed 字段")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(tasks)")
        columns_after = [row[1] for row in cursor.fetchall()]
        if "is_completed" in columns_after:
            print("✓ 验证成功：is_completed 字段已添加到 tasks 表")
        else:
            print("⚠ 警告：无法验证字段是否添加成功")
    
    conn.commit()
    print("\n迁移成功！")
    print("- 已为 tasks 表添加 is_completed 字段")
    print("- 默认值：0 (未完成)")
    print("- 说明：此字段用于标记任务完成状态，实现软删除功能")
    
    conn.close()
    
except Exception as e:
    print(f"\n迁移失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

