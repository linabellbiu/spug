# Webhook 功能升级说明

## 概述

本次升级将 Webhook 功能从**部署配置维度**改为**应用维度**，支持在应用级别配置不同环境的分支匹配规则。这样可以实现：
- 一个应用只需要配置一个 Webhook URL
- 不同环境可以配置不同的分支匹配规则
- Git 推送不同分支时，自动触发对应环境的部署

## 主要变更

### 1. 数据库变更
- 在 `apps` 表中添加 `webhook_config` 字段（TEXT类型），用于存储 JSON 格式的 Webhook 配置
- 配置格式：`{"环境ID": "分支匹配规则", ...}`

### 2. API 接口变更
- Webhook URL 从 `/api/apis/deploy/{deploy_id}/` 改为 `/api/apis/deploy/{app_id}/`
- 新增接口：
  - `GET /api/app/webhook/config/?app_id={app_id}` - 获取应用的 Webhook 配置
  - `POST /api/app/webhook/config/` - 保存应用的 Webhook 配置

### 3. 前端界面变更
- Webhook 按钮从部署配置列表移至应用列表
- Webhook 配置弹窗新增环境分支配置功能
- 支持为每个环境配置独立的分支匹配规则

## 使用方法

### 1. 执行数据库迁移

```bash
# 进入数据库
mysql -u your_username -p your_database

# 或者使用 PostgreSQL
psql -U your_username -d your_database

# 执行迁移脚本
source /path/to/spug/docs/add_webhook_config.sql
```

### 2. 重启服务

```bash
# 重启后端服务
cd spug_api
python manage.py runserver

# 重启前端服务（如果需要）
cd spug_web
npm start
```

### 3. 配置 Webhook

1. 在应用列表中，点击应用的 **Webhook** 按钮
2. 复制 Webhook URL 和 Secret Token
3. 在 Git 仓库中配置 Webhook：
   - URL: 复制的 Webhook URL
   - Secret/Token: 复制的 Secret Token
   - 触发事件: Push events, Tag push events, Merge Request events
4. 配置环境分支规则：
   - 为每个环境配置对应的分支匹配规则
   - 支持精确匹配、通配符和正则表达式

### 4. 分支匹配规则示例

- **精确匹配**: `master` - 只匹配 master 分支
- **通配符**: `feature/*` - 匹配所有 feature/ 开头的分支
- **正则表达式**: `^release/.*$` - 匹配所有 release/ 开头的分支
- **全部匹配**: `*` - 匹配所有分支

### 5. 配置示例

假设有以下环境：
- 开发环境（env_id: 1）
- 测试环境（env_id: 2）
- 生产环境（env_id: 3）

配置如下：
```json
{
  "1": "dev",           // 开发环境匹配 dev 分支
  "2": "test",          // 测试环境匹配 test 分支
  "3": "master"         // 生产环境匹配 master 分支
}
```

或者使用通配符：
```json
{
  "1": "feature/*",     // 开发环境匹配所有 feature 分支
  "2": "release/*",     // 测试环境匹配所有 release 分支
  "3": "master"         // 生产环境匹配 master 分支
}
```

## 工作流程

1. 开发人员推送代码到 Git 仓库
2. Git 仓库触发 Webhook，调用 Spug 的 Webhook URL
3. Spug 接收到 Webhook 请求，解析分支信息
4. 根据应用的 webhook_config 配置，匹配对应的环境
5. 如果匹配成功，创建部署请求并自动触发部署

## 注意事项

1. **兼容性**: 旧的 Webhook URL 仍然可以使用，但建议迁移到新的应用级别 URL
2. **权限**: 需要 `deploy.app.config` 权限才能配置 Webhook
3. **分支匹配**: 如果多个环境的分支规则都匹配，会同时触发多个环境的部署
4. **正则表达式**: 使用正则表达式时，确保语法正确，否则会回退到精确匹配

## 故障排查

### Webhook 未触发部署
1. 检查 Webhook URL 是否正确（应该是应用级别的 URL）
2. 检查 Secret Token 是否配置正确
3. 检查环境分支配置是否匹配推送的分支
4. 查看 Spug 后端日志，确认是否收到 Webhook 请求

### 分支匹配不生效
1. 检查分支匹配规则是否正确
2. 确认环境 ID 是否正确
3. 尝试使用精确匹配测试

### 多个环境同时触发
1. 检查分支匹配规则是否有重叠
2. 调整规则，确保每个分支只匹配一个环境

## 技术细节

### 分支匹配逻辑
```python
def _match_branch(branch, pattern):
    if not pattern:
        return False
    
    pattern = pattern.strip()
    if not pattern:
        return False
    
    # 通配符匹配
    if pattern == '*':
        return True
    
    # 正则表达式匹配
    try:
        return re.match(pattern, branch) is not None
    except Exception:
        # 回退到精确匹配
        return branch == pattern
```

### 数据结构
```python
# App 模型
class App(models.Model):
    webhook_config = models.TextField(null=True)  # JSON 格式
    
# webhook_config 示例
{
    "1": "dev",
    "2": "test", 
    "3": "master"
}
```

## 回滚方案

如果需要回滚到旧版本：

1. 恢复代码到升级前的版本
2. 数据库不需要回滚（webhook_config 字段可以保留，不影响旧版本）
3. 重启服务

## 支持的 Git 平台

- Gitee
- Github
- Gitlab
- Gogs
- Coding
- Codeup (阿里云)

所有平台均支持：
- Branch Push 事件
- Tag Push 事件
- Merge Request/Pull Request 事件
