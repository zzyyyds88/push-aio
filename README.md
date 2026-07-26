# push-aio

个人统一推送平台：把一批通知渠道（Bark / 邮箱 / Telegram / 钉钉 / 飞书 / ...）聚合起来对外暴露**一个**鉴权入口，自动做主→备→紧急三层故障切换。

定位：**个人自用**，不负责向第三方分发。所有渠道配置的都是你自己的设备。

## 设计要点

- **接口分离**：外部调用入口与 WebUI 管理入口物理拆开，管理接口不对外。
  - `/api/health`：公开，仅探活。
  - `/api/notify`：外部程序调用，需 API Key，**只接受消息内容**，不能选渠道、不能指定优先级。
  - `/admin/api/*`：WebUI 专用，需 API Key，含渠道 CRUD、日志、测试发送。前端访问，不对外公开。
- **固定调度策略**：外部调用方没有"normal/emergency"可选，系统统一按 `主通道 → 备用通道 → 全失败升级紧急通道` 执行。
- **严格模式**：`/api/notify` 启用 `extra="forbid"`，多传一个字段直接 422，防止外部调用方绕过调度策略。
- **强制鉴权**：未配置 API Key 拒绝启动；除 `/api/health` 外所有接口需 `X-API-Key` 请求头。
- **固定端口 8080**：不接受 CLI/环境变量覆盖。

## 目录结构

```
push-aio/
├── src/push_aio/                # FastAPI 后端（src layout）
│   ├── api/routes.py            # 三层路由：public / notify / admin
│   ├── services/dispatcher.py   # 主→备→紧急调度核心
│   ├── services/channels/       # 渠道注册表 + 各渠道 sender
│   ├── core/security.py         # API Key 鉴权
│   ├── core/db.py               # SQLite + create_all 建表
│   ├── static/                  # 液态玻璃质感单页前端
│   └── main.py                  # 入口（端口固定 8080）
├── data/                        # 运行时数据（已 .gitignore）
│   ├── push_aio.db              # SQLite 数据库
│   └── bootstrap_channels.json  # 可选初始化种子
├── .env                         # API Key 配置（已 .gitignore）
├── .env.example                 # 配置示例
└── pyproject.toml
```

## 安装

需要 Python 3.11+。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 配置 API Key（必填）

服务设计为公网部署，未配置 API Key 会拒绝启动。

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

## 启动

```powershell
python -m push_aio.main
```

启动后访问：

- 前端 WebUI：`http://127.0.0.1:8080/`（首次访问弹窗输入 API Key）
- API 文档：`http://127.0.0.1:8080/docs`

## 推送调度机制

每个渠道可单独配置：

- `backup_channel_ids`：备用组（id 列表）。主通道失败时按顺序逐个尝试。
- `is_emergency`：是否标记为紧急通道。仅当所有主链全部失败时才会自动升级到这些通道。
- `priority`：同层通道内的尝试顺序（数字越小越先尝试，默认 100）。

### 固定调度流程

```
任何 /api/notify 调用（外部程序）或 /admin/api/notify（WebUI 测试）
  ├─ 1. 找出所有启用的非紧急通道（按 priority 升序）作为主通道
  ├─ 2. 对每个主通道 c：
  │     ├─ 尝试 c 本身
  │     └─ 失败 → 按 c.backup_channel_ids 顺序尝试备用
  │           └─ 任一备用成功即停止该链
  └─ 3. 所有主链全失败 且 存在启用的紧急通道
        └─ 自动升级，逐个尝试紧急通道
```

- 同一次请求内**每个通道最多尝试一次**（去重），避免环路。
- 瞬时网络异常（Timeout / ConnectionError）会重试 1 次。
- 所有尝试写入 `delivery_logs`，共享同一个 `request_id`，并标记 `role`（primary / backup / emergency）和 `original_channel_id`。

## 渠道配置

渠道的增删改**只能在 WebUI 进行**，没有对外管理 API。

每个渠道有两种目标模式：

- `embedded`：设备码 / token / chat_id 已嵌入到 `config` 里，不需要 `default_target`（Bark、Telegram、钉钉、飞书等都属于这种）。
- `external`：目标收件人独立于配置，需要填 `default_target`（目前只有 email）。

支持渠道：`bark`、`email`、`telegram_bot`、`dingtalk_bot`、`feishu_bot`、`pushplus`、`server_chan`、`pushdeer`、`gotify`、`ntfy`、`wxpusher`、`wecom_bot`、`wecom_app`、`qmsg`、`weplus_bot`、`aibotk`、`pushme`、`chronocat`、`synology_chat`、`go_cqhttp`、`igot`、`webhook`、`console`。

## 批量初始化渠道

如果你已经有一批渠道配置，可以先创建 `data/bootstrap_channels.json`，服务首次启动且数据库为空时会自动导入。示例见 `data/bootstrap_channels.example.json`。

## API 速查

### 公开接口

| 方法 | 路径 | 鉴权 | 用途 |
|---|---|---|---|
| GET | `/api/health` | 否 | 健康检查 / 监控探活 |

### 外部调用接口（程序用）

| 方法 | 路径 | 鉴权 | 用途 |
|---|---|---|---|
| POST | `/api/notify` | 是 | 外部程序投递通知 |

`/api/notify` 请求体（严格模式，多传字段直接 422）：

```json
{
  "title": "任务完成",
  "content": "已执行完毕",
  "content_type": "plain"
}
```

`content_type` 可选 `plain` / `markdown` / `html`，默认 `plain`。需要附件时传 `attachments`（目前仅 email 渠道支持）。

调用示例：

```powershell
curl -X POST http://your-host:8080/api/notify `
  -H "X-API-Key: <你的 key>" `
  -H "Content-Type: application/json" `
  -d '{\"title\":\"任务完成\",\"content\":\"已执行完毕\"}'
```

响应体：

```json
{
  "success": true,
  "request_id": "8e0f...c1",
  "escalated": false,
  "chains": [
    {
      "primary": { "channel_id": 1, "channel_name": "我的 Bark", "success": true, "role": "primary", "detail": "..." },
      "backups": [],
      "success": true,
      "final_role": "primary"
    }
  ],
  "emergency_attempts": [],
  "results": [ ... ]
}
```

`escalated=true` 表示主链全部失败、已自动升级到紧急通道。

### 管理接口（WebUI 专用）

> 这些接口只供前端 WebUI 使用，不对外公开文档。外部程序只需要 `/api/notify`。

包含：渠道类型元信息、渠道 CRUD、备用组更新、单通道测试发送、平台总览状态、日志查询、WebUI 测试发送。所有路径前缀 `/admin/api/`，需 `X-API-Key`。

WebUI 已封装好全部管理操作，无需手动调用这些接口。
