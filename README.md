# push-aio

从 `example/qinglong-develop` 提取通知能力后，重写成的 Python 聚合通知平台。
**v0.2** 加入主→备→紧急三层故障切换调度引擎，并重构为液态玻璃 UI。

当前已按 `example/qinglong-develop/sample/notify.py` 提取这些渠道：

`bark`、`console`、`dingtalk_bot`、`feishu_bot`、`go_cqhttp`、`gotify`、`igot`、`server_chan`、`pushdeer`、`synology_chat`、`pushplus`、`weplus_bot`、`qmsg`、`wecom_app`、`wecom_bot`、`telegram_bot`、`aibotk`、`email`、`pushme`、`chronocat`、`webhook`、`ntfy`、`wxpusher`。

能力审计见 `docs/CHANNEL_CAPABILITY_AUDIT.md`。

## 目录

- `src/push_aio`：FastAPI 后端、调度引擎、渠道注册表、SQLite 持久化（src layout）。
- `src/push_aio/services/dispatcher.py`：主→备→紧急三层调度核心。
- `src/push_aio/static`：液态玻璃质感单页前端，由后端直接托管。
- `data/push_aio.db`：运行后自动生成的 SQLite 数据库（已 .gitignore，不上传）。
- `data/bootstrap_channels.json`：可选初始化种子文件，仅在数据库为空时导入（已 .gitignore，私有配置不上传）。
- `data/bootstrap_channels.example.json`：脱敏示例，可参考。
- `example/`：上游参考源码副本（青龙），已 .gitignore，不开源上传；上游链接：https://github.com/whyour/qinglong

## 安装

需要本地有 Python 3.11+。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

`pip install -e .` 会按 `pyproject.toml` 安装依赖并以可编辑模式注册 `push_aio` 包。

## 配置 API Key（必填）

本服务设计为公网部署，所有 `/api/*` 接口（`/api/health` 除外）都需要 API Key 鉴权，未配置则拒绝启动。

1. 复制示例配置：

```powershell
cp .env.example .env
```

2. 生成随机 Key 并填入 `.env`：

```powershell
# PowerShell 生成 32 位随机串
-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | % {[char]$_})
```

3. 编辑 `.env`：

```
PUSH_AIO_API_KEY=<你刚生成的随机串>
```

`.env` 已在 `.gitignore` 中，不会上传到 git。

## 启动（固定端口 8080）

```powershell
python -m push_aio.main
```

或：

```powershell
uvicorn push_aio.main:app --host 0.0.0.0 --port 8080 --reload
```

启动后访问：

- 前端：`http://127.0.0.1:8080/`
- API 文档：`http://127.0.0.1:8080/docs`

## 推送调度机制

每个渠道可单独配置：

- `backup_channel_ids`：备用组（id 列表）。主通道失败时按顺序逐个尝试。
- `is_emergency`：紧急通道标记。`normal` 请求主链全部失败后自动升级到这些通道；`emergency` 请求会与主链**并发**触发这些通道。
- `priority`：优先级（数字越小越先尝试）。

### 调度流程

```
正常请求 (priority=normal)
  ├─ 1. 按筛选条件找出主通道
  ├─ 2. 对每个主通道 c：
  │     ├─ 尝试 c 本身
  │     └─ 失败 → 按 c.backup_channel_ids 顺序尝试备用
  │           └─ 任一备用成功即停止该链
  └─ 3. 所有主链全失败 且 存在紧急通道 → 自动升级，逐个尝试紧急通道

紧急请求 (priority=emergency 或 force_emergency=true)
  ├─ 1. 同上跑主链
  └─ 2. 同时并发触发所有紧急通道（不等主链失败）
```

每个通道单次请求内**最多尝试一次**（去重），瞬时网络异常会重试 1 次。所有尝试写入 `delivery_logs`，同一次调用共享 `request_id`，并标记 `role`（primary/backup/emergency）和 `original_channel_id`。

## 批量初始化渠道

如果你已经有一批渠道配置，可以先创建 `data/bootstrap_channels.json`，服务首次启动且数据库为空时会自动导入。示例见 `data/bootstrap_channels.example.json`。

## API 速查

> 所有 `/api/*` 接口（`/api/health` 除外）都需要在请求头携带 `X-API-Key: <你的 key>`。前端首次访问会弹窗输入并存到 localStorage，外部程序调用时手动加这个 header。

### 新增渠道

```http
POST /api/channels
```

```json
{
  "name": "我的 Bark",
  "type": "bark",
  "enabled": true,
  "default_target": null,
  "config": { "bark_base_url": "https://api.day.app/你的设备码" },
  "backup_channel_ids": [2, 3],
  "is_emergency": false,
  "priority": 100
}
```

### 更新备用组（单独接口）

```http
PUT /api/channels/{channel_id}/backups
```

```json
{ "backup_channel_ids": [2, 3] }
```

### 远程触发通知

```http
POST /api/notify
X-API-Key: <你的 key>
Content-Type: application/json
```

最简形式（发给所有启用的主通道）：

```json
{ "title": "任务完成", "content": "已执行完毕" }
```

紧急发送（主链 + 紧急通道并发）：

```json
{
  "title": "服务器宕机告警",
  "content": "node-3 失联超过 60s",
  "priority": "emergency"
}
```

强制并发触发紧急通道（即便主链命中也并发）：

```json
{
  "title": "严重告警",
  "content": "数据库连接耗尽",
  "force_emergency": true
}
```

按类型/名称筛选、覆盖目标、覆盖配置（与 v0.1 一致）：

```json
{
  "title": "仅发邮件",
  "content": "只发给指定邮箱",
  "channel_ids": [2],
  "target_overrides": { "2": "your-account@example.com" },
  "config_overrides": {
    "1": { "bark_group": "任务通知", "bark_sound": "bell" }
  }
}
```

响应体新增**链路可视化字段**：

```json
{
  "success": true,
  "request_id": "8e0f...c1",
  "priority": "normal",
  "escalated": false,
  "chains": [
    {
      "primary": { "channel_id": 1, "channel_name": "我的 Bark", "success": false, "role": "primary", "detail": "..." },
      "backups": [
        { "channel_id": 2, "channel_name": "QQ邮箱1", "success": true, "role": "backup", "original_channel_id": 1, "detail": "..." }
      ],
      "success": true,
      "final_role": "backup"
    }
  ],
  "emergency_attempts": [],
  "results": [ ... ]
}
```

### 查询

- `GET /api/status`：平台总览（含 `emergency_count`）。
- `GET /api/channels`：所有渠道（含 `backup_channel_ids` / `is_emergency` / `priority`）。
- `GET /api/channels/emergency`：紧急通道列表。
- `GET /api/channels/status`：每个渠道本地校验状态。
- `GET /api/logs`：最近 50 条发送日志。
- `GET /api/logs/{request_id}`：按请求 ID 聚合的所有尝试日志。
- `POST /api/channels/{channel_id}/test`：单通道测试发送（不走备用/紧急链路）。

## 你当前给的渠道如何录入

你给的两组 QQ 邮箱参数里，只有 `imap_host` / `imap_port`，但发送邮件实际要走 `SMTP`。QQ 邮箱通常可直接改成：

- `smtp_host`: `smtp.qq.com`
- `smtp_port`: `465`
- `use_ssl`: `true`

`imap_host` 会被后端兼容转换为 `smtp_host`，但推荐直接保存为 `smtp.qq.com` + `465` + `use_ssl: true`。
