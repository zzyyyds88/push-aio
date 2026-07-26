# PushHub

个人统一推送平台：把一批通知渠道（Bark / 邮箱 / Telegram / 钉钉 / 飞书 / ...）聚合起来对外暴露**一个**鉴权入口，自动做主→备→紧急三层故障切换。

定位：**个人自用**，不负责向第三方分发。所有渠道配置的都是你自己的设备。

## 设计要点

- **接口分离**：外部调用入口与 WebUI 管理入口物理拆开，管理接口不对外。
  - `/api/health`：公开，仅探活。
  - `/api/notify`：外部程序调用，需 API Key，**只接受消息内容**，不能选渠道、不能指定优先级。
  - `/admin/api/*`：WebUI 专用，需 API Key，含渠道 CRUD、日志、测试发送。前端访问，不对外公开。
- **固定调度策略**：外部调用方没有"normal/emergency"可选，系统统一按 `同类型层级(主推送 → 备用1 → 备用2 ...)逐个尝试 → 全失败升级全局紧急层级(并发发送)` 执行。
- **严格模式**：`/api/notify` 启用 `extra="forbid"`，多传一个字段直接 422，防止外部调用方绕过调度策略。
- **配置全部入库**：API Key 存在 SQLite 的 `settings` 表中，**不使用 `.env`**。首次启动由 WebUI 引导设置 Key，修改后立即生效、无需重启。
- **固定端口 8080**：不接受 CLI/环境变量覆盖。
- **格式兼容层**：调用方传 `plain` / `markdown` / `html`，兼容层按各渠道能力自动适配或降级，每个渠道仍按自身 API 原生格式构造 payload，**不统一 payload 结构、不舍弃原有能力**。

## 目录结构

```
pushhub/
├── src/pushhub/                   # FastAPI 后端（src layout）
│   ├── api/routes.py              # 三层路由：public / notify / admin
│   ├── services/
│   │   ├── dispatcher.py          # 主→备→紧急调度核心
│   │   ├── channels.py            # 渠道注册表 + 23 个渠道 sender
│   │   └── format_adapter.py      # 消息格式兼容层（plain/markdown/html 互转）
│   ├── core/
│   │   ├── security.py            # API Key 鉴权（Key 存 DB）
│   │   └── db.py                  # SQLite + create_all 建表
│   ├── static/                    # 液态玻璃质感单页前端
│   │   ├── index.html             # WebUI 主界面
│   │   ├── help.html              # /api/help 调用说明页
│   │   ├── app.js                 # 前端逻辑
│   │   └── styles.css             # 样式
│   ├── models.py                  # SQLAlchemy 模型
│   ├── schemas.py                 # Pydantic schema
│   └── main.py                    # 入口（端口固定 8080）
├── docs/
│   ├── channel-docs/              # 12 份渠道官方文档本地化（能力声明依据）
│   └── ERROR_CODES.md             # 错误码说明
├── data/                          # 运行时数据（已 .gitignore）
│   └── pushhub.db                # SQLite 数据库（含 channels / delivery_logs / settings）
├── API_CALLING.md                 # 外部调用说明（与 /api/help 页同步）
└── pyproject.toml
```

## 安装

需要 Python 3.11+。

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 首次启动

直接运行，不需要预先准备任何配置文件：

```powershell
python -m pushhub.main
```

- 数据库无 API Key 时进入 **setup 模式**：浏览器访问 `http://127.0.0.1:8080/`，按页面引导设置 API Key（即 WebUI 登录密码 + 外部调用 `X-API-Key`，同一把）。
- 设置后即可登录 WebUI 管理渠道，或用该 Key 调用 `/api/notify`。
- 修改 Key：WebUI「系统设置」页 → 改密码表单，写入 DB 后立即生效、无需重启。

> 不使用 `.env`、不读取环境变量、不使用 bootstrap 种子文件。所有配置（渠道、API Key）均存于 `data/pushhub.db`，渠道通过 WebUI 录入。

## 启动后访问入口

- WebUI：`http://127.0.0.1:8080/`（首次访问需设置或登录 API Key）
- 调用说明页：`http://127.0.0.1:8080/api/help`
- 健康检查：`http://127.0.0.1:8080/api/health`
- OpenAPI 文档：`http://127.0.0.1:8080/docs`

## 推送调度机制

调度分两层依次补位：

- **同类型层级**：`is_emergency=False` 的启用渠道，按 `channel_type` 分组，组内按 `priority` 升序逐个尝试（主推送 → 备用1 → 备用2 ...）。
- **全局紧急层级**：`is_emergency=True` 的启用渠道，仅当同类型层级全失败时自动升级（全局兜底，不按渠道类型筛选，所有紧急渠道并发发送）。

顺序调整通过 WebUI 的「上移 / 下移」按钮完成，用户**无需手填 `priority`**。

### 固定调度流程

```
任何 /api/notify 调用（外部程序）或 /admin/api/notify（WebUI 测试）
  ├─ 1. 找出该类型所有启用的非紧急渠道（按 priority 升序）组成同类型层级
  │      （主推送 → 备用1 → 备用2 ...）
  ├─ 2. 按顺位逐个尝试同类型层级：任一成功即停止
  └─ 3. 同类型层级全部失败 且 存在启用的紧急渠道
        └─ 自动升级到全局紧急层级（不按 channel_type 筛选，所有紧急渠道并发发送）
```

- 同一次请求内**每个通道最多尝试一次**（去重），避免环路。
- 瞬时网络异常（Timeout / ConnectionError）会重试 1 次。
- 切换决策基于错误分类：
  - `rate_limit`(限流) / `auth`(认证) / `config`(配置) / `channel_error`(业务错误) → 不重试，立即切下一个通道
  - `network`(网络异常) → 重试 1 次后切下一个通道
- 所有尝试写入 `delivery_logs`，共享同一个 `request_id`，标记 `role`（`primary` / `backup` / `emergency`）和 `error_kind`。

### 响应总结字段

`/api/notify` 响应包含以下让调用方一眼看出最终结果的字段：

| 字段 | 说明 |
|---|---|
| `success` | 整体是否投递成功 |
| `final_role` | 最终成功投递的角色：`primary`(主推送，第 1 顺位就成功) / `backup`(同类型层级前面有失败靠后面备用成功) / `emergency`(同类型层级全失败靠紧急渠道成功)。全失败时为 `null` |
| `final_channel_id` / `final_channel_name` / `final_channel_type` | 最终成功投递的渠道信息（全失败时为 `null`） |
| `total_attempts` | 本次请求总共尝试的渠道数（含失败 + 成功） |
| `escalated` | `true` 表示同类型层级全失败、已自动升级到全局紧急层级 |
| `error_kind` | 失败时的错误分类 |

完整字段说明见 [API_CALLING.md](API_CALLING.md) 或 `/api/help` 页。

## 消息格式兼容层

调用方传 `content_type`（`plain` / `markdown` / `html`），兼容层按各渠道能力自动适配：

- 渠道支持请求格式 → 直接使用
- 渠道不支持 → 降级到该渠道的偏好格式（如 PushPlus 偏好 `html`、Server 酱偏好 `markdown`）

各渠道的 `supported_formats` 和 `preferred_format` 基于**官方文档核实**，文档本地化保存在 [docs/channel-docs/](docs/channel-docs/)。调用方可通过 `GET /admin/api/channel-types` 程序化获取，或查阅 [API_CALLING.md 的渠道格式支持矩阵](API_CALLING.md#渠道格式支持矩阵)。

每个渠道按自身 API 原生格式构造 payload（如钉钉的 `text`/`markdown` msgtype、企业微信的 `markdown` msgtype、Telegram 的 `MarkdownV2`/`HTML` parse_mode、邮件的 `plain`/`html` body 等），**不统一 payload 结构、保留各渠道原有能力**。

## 渠道配置

渠道的增删改**只能在 WebUI 进行**，没有对外管理 API。

每个渠道有两种目标模式：

- `embedded`：设备码 / token / chat_id 已嵌入到 `config` 里，不需要 `default_target`（Bark、Telegram、钉钉、飞书等都属于这种）。
- `external`：目标收件人独立于配置，需要填 `default_target`（目前只有 email）。

保存渠道前可点「测试」按钮预检，配置可用再保存，避免存入无效渠道。

支持渠道（共 23 个）：`bark`、`email`、`telegram_bot`、`dingtalk_bot`、`feishu_bot`、`pushplus`、`server_chan`、`pushdeer`、`gotify`、`ntfy`、`wxpusher`、`wecom_bot`、`wecom_app`、`qmsg`、`weplus_bot`、`aibotk`、`pushme`、`chronocat`、`synology_chat`、`go_cqhttp`、`igot`、`webhook`、`console`。

## API 速查

### 公开接口

| 方法 | 路径 | 鉴权 | 用途 |
|---|---|---|---|
| GET | `/api/health` | 否 | 健康检查 / 监控探活 |
| GET | `/api/help` | 否 | 调用说明页（HTML） |

### 外部调用接口（程序用）

| 方法 | 路径 | 鉴权 | 用途 |
|---|---|---|---|
| POST | `/api/notify` | 是 | 外部程序投递通知 |

`/api/notify` 请求体（严格模式，多传字段直接 422）：

```json
{
  "title": "任务完成",
  "content": "已执行完毕",
  "content_type": "plain",
  "channel_type": "dingtalk_bot"
}
```

- `content_type` 可选 `plain` / `markdown` / `html`，默认 `plain`。
- `channel_type` 可选，指定后仅在该类型的启用渠道里走调度；不传则走所有渠道全局调度。外部程序只需知道"我要钉钉推送"，不需知道具体渠道 ID。
- 需要附件时传 `attachments`（目前仅 email 渠道支持）。

调用示例：

```powershell
curl -X POST http://127.0.0.1:8080/api/notify `
  -H "X-API-Key: <你的 key>" `
  -H "Content-Type: application/json" `
  -d '{\"title\":\"任务完成\",\"content\":\"已执行完毕\"}'
```

完整请求 / 响应字段说明、调用示例（curl / PowerShell / Python）、渠道格式支持矩阵见 [API_CALLING.md](API_CALLING.md)。

### 管理接口（WebUI 专用）

> 这些接口只供前端 WebUI 使用，不对外公开。外部程序只需要 `/api/notify`。

包含：渠道类型元信息、渠道 CRUD、顺序调整、单通道测试、保存前试发、平台总览状态、日志查询、WebUI 测试发送。所有路径前缀 `/admin/api/`，需 `X-API-Key`。WebUI 已封装好全部管理操作，无需手动调用这些接口。
