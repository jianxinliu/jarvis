-- 迁移脚本：为 reminder_logs 表添加 app_id 字段
-- 执行日期：2025-01-XX
-- 说明：添加 app_id 字段用于标识提醒来自哪个应用

-- ============================================
-- SQLite 版本
-- ============================================

-- 添加 app_id 字段
ALTER TABLE reminder_logs ADD COLUMN app_id VARCHAR(100);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_reminder_logs_app_id ON reminder_logs (app_id);

-- 根据现有数据更新 app_id（可选，用于历史数据）
-- 根据 reminder_type 自动设置 app_id
UPDATE reminder_logs 
SET app_id = 'tasks' 
WHERE reminder_type IN ('interval', 'daily', 'subtask') AND app_id IS NULL;

UPDATE reminder_logs 
SET app_id = 'todo' 
WHERE reminder_type IN ('todo', 'todo_daily') AND app_id IS NULL;

-- ============================================
-- PostgreSQL 版本
-- ============================================
-- 如果使用 PostgreSQL，请使用以下 SQL：

/*
-- 添加 app_id 字段
ALTER TABLE reminder_logs 
ADD COLUMN app_id VARCHAR(100);

-- 创建索引
CREATE INDEX IF NOT EXISTS ix_reminder_logs_app_id ON reminder_logs (app_id);

-- 添加注释
COMMENT ON COLUMN reminder_logs.app_id IS '来源应用ID';

-- 根据现有数据更新 app_id（可选，用于历史数据）
UPDATE reminder_logs 
SET app_id = 'tasks' 
WHERE reminder_type IN ('interval', 'daily', 'subtask') AND app_id IS NULL;

UPDATE reminder_logs 
SET app_id = 'todo' 
WHERE reminder_type IN ('todo', 'todo_daily') AND app_id IS NULL;
*/

-- ============================================
-- MySQL 版本（如果将来需要）
-- ============================================
/*
-- 添加 app_id 字段
ALTER TABLE reminder_logs 
ADD COLUMN app_id VARCHAR(100) NULL COMMENT '来源应用ID';

-- 创建索引
CREATE INDEX ix_reminder_logs_app_id ON reminder_logs (app_id);

-- 根据现有数据更新 app_id（可选，用于历史数据）
UPDATE reminder_logs 
SET app_id = 'tasks' 
WHERE reminder_type IN ('interval', 'daily', 'subtask') AND app_id IS NULL;

UPDATE reminder_logs 
SET app_id = 'todo' 
WHERE reminder_type IN ('todo', 'todo_daily') AND app_id IS NULL;
*/

-- ============================================
-- 验证脚本（可选）
-- ============================================
-- 检查字段是否添加成功
-- SQLite:
-- PRAGMA table_info(reminder_logs);

-- PostgreSQL:
-- SELECT column_name, data_type, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'reminder_logs' AND column_name = 'app_id';

-- MySQL:
-- DESCRIBE reminder_logs;

