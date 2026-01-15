-- 添加webhook_config字段到apps表
-- 该字段用于存储应用级别的webhook配置，格式为JSON
-- 键为环境ID，值为分支匹配规则

ALTER TABLE apps ADD COLUMN webhook_config TEXT DEFAULT NULL;

-- 添加注释
COMMENT ON COLUMN apps.webhook_config IS 'Webhook配置，JSON格式，键为环境ID，值为分支匹配规则';
