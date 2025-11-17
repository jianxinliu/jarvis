#!/usr/bin/env python3
"""数据库迁移脚本：为 excel_analysis_records 表添加 file_content 字段."""

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
    
    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(excel_analysis_records)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if "file_content" in columns:
        print("字段 file_content 已存在，跳过迁移")
        conn.close()
        sys.exit(0)
    
    # 添加新列
    print("正在添加 file_content 字段...")
    cursor.execute("""
        ALTER TABLE excel_analysis_records 
        ADD COLUMN file_content BLOB
    """)
    
    conn.commit()
    print("迁移成功！已添加 file_content 字段")
    
    conn.close()
    
except Exception as e:
    print(f"迁移失败: {e}")
    sys.exit(1)

