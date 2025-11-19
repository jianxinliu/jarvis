-- 迁移脚本：为 tasks 表添加 is_completed 字段
-- 执行日期：2025-01-XX
-- 说明：将任务删除改为软删除，添加 is_completed 字段标记任务完成状态

-- ============================================
-- SQLite 版本
-- ============================================
-- SQLite 中 BOOLEAN 类型实际上是 INTEGER (0 或 1)

-- 添加 is_completed 字段
ALTER TABLE tasks ADD COLUMN is_completed INTEGER NOT NULL DEFAULT 0;

-- 添加注释（SQLite 不支持列注释，但可以在迁移脚本中记录）
-- is_completed: 是否已完成 (0=未完成, 1=已完成)

-- ============================================
-- PostgreSQL 版本
-- ============================================
-- 如果使用 PostgreSQL，请使用以下 SQL：

/*
-- 添加 is_completed 字段
ALTER TABLE tasks 
ADD COLUMN is_completed BOOLEAN NOT NULL DEFAULT FALSE;

-- 添加注释
COMMENT ON COLUMN tasks.is_completed IS '是否已完成';
*/

-- ============================================
-- MySQL 版本（如果将来需要）
-- ============================================
/*
-- 添加 is_completed 字段
ALTER TABLE tasks 
ADD COLUMN is_completed BOOLEAN NOT NULL DEFAULT FALSE 
COMMENT '是否已完成';
*/

-- ============================================
-- 验证脚本（可选）
-- ============================================
-- 检查字段是否添加成功
-- SQLite:
-- PRAGMA table_info(tasks);

-- PostgreSQL:
-- SELECT column_name, data_type, column_default, is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'tasks' AND column_name = 'is_completed';

-- MySQL:
-- DESCRIBE tasks;

