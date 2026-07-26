# PushHub · 外部调用说明

本文档面向**外部程序调用方**。WebUI 管理操作请直接访问 `http://<your-host>:8080/`。

> 在线版本：服务启动后访问 `http://<your-host>:8080/api/help`。

## 接口概览

| 方法 | 路径 | 鉴权 | 用途 |
|---|---|---|---|
| GET | `/api/health` | 无 | 健康检查 / 监控探活 |
| GET | `/api/help` | 无 | 调用说明页（HTML） |
| POST | `/api/notify` | `X-API-Key` | 投递通知（外部程序唯一入口） |

> 管理接口（渠道增删改、日志查看）只供 WebUI 使用，**不对外公开**。所有配置变更必须登录 WebUI 操作。

## 鉴权

所有需要鉴权的接口都必须在请求头携带：

```
X-API-Key: <你的 API Key>
```

API Key 与 WebUI 登录密码是**同一把**，保存在数据库的 `settings` 表中。**首次启动时数据库无 Key，需访问 WebUI 完成初始化设置**；设置后即可用于登录与外部调用。可在 WebUI「系统设置」页修改，修改后立即生效、无需重启。

> 首次启动尚未设置 Key 时，除 `GET /api/health`、`GET /api/help`、`GET /admin/api/auth/status`、`POST /admin/api/auth/setup` 外的所有接口都会返回 `401`，提示先完成初始化。

未携带或携带错误返回 `401 Unauthorized`：

```json
{"detail": "无效或缺失的 API Key。请在请求头携带 X-API-Key。"}
```

## 投递通知

### 请求

```
POST /api/notify
Content-Type: application/json
X-API-Key: <你的 API Key>
```

### 请求体（严格模式）

请求体启用 `extra=forbid` 严格模式，**多传任何字段都会被拒绝（422）**，防止外部调用方绕过系统调度策略。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `title` | string | 是 | 通知标题，1-255 字符 |
| `content` | string | 是 | 通知正文 |
| `content_type` | string | 否 | `plain` / `markdown` / `html`，默认 `plain` |
| `attachments` | array | 否 | 附件列表（目前仅 email 渠道支持） |
| `channel_type` | string | 是 | 必填：渠道类型（如 `bark` / `dingtalk_bot` / `feishu_bot`）。本系统按类型调度，不存在"全局主推送渠道"——调用方必须明确要发到哪种渠道。系统在该类型的启用非紧急渠道里按 priority 逐个尝试（主推送 → 备用1 → 备用2 ...），全失败再升级到全局紧急层级（并发发送） |
| `extra` | object | 否 | 渠道特有的内容字段，透传给渠道。key 用渠道**原生 API 字段名**（非项目自定义命名），调用方通过 `GET /admin/api/channel-types` 查看各渠道 `extra_schema`。详见下方[渠道内容字段（extra）矩阵](#渠道内容字段extra矩阵) |

> `extra` 不影响调度策略，仅透传给渠道用于构造 payload。渠道配置（DB）只保留连接凭证（token、url 等），内容字段全部通过 `extra` 按消息传递，与各渠道原生调用机制一致。

### 调用示例

**curl**

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"任务完成","content":"已执行完毕","channel_type":"dingtalk_bot"}'
```

**Markdown 内容**

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"构建报告","content":"## 详情\n- 成功 12\n- 失败 0","content_type":"markdown","channel_type":"dingtalk_bot"}'
```

**指定渠道类型 + extra 透传（Bark 带副标题和声音）**

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"报警","content":"CPU 超过 90%","channel_type":"bark","extra":{"subtitle":"服务器告警","sound":"alarm","group":"监控"}}'
```

**PowerShell**

```powershell
Invoke-WebRequest -Uri http://<your-host>:8080/api/notify `
  -Method POST `
  -Headers @{ "X-API-Key" = "<你的 key>" } `
  -ContentType "application/json" `
  -Body '{"title":"任务完成","content":"已执行完毕","channel_type":"dingtalk_bot"}'
```

**Python（requests）**

```python
import requests

resp = requests.post(
    "http://<your-host>:8080/api/notify",
    headers={"X-API-Key": "<你的 key>"},
    json={"title": "任务完成", "content": "已执行完毕", "channel_type": "dingtalk_bot"},
)
print(resp.json())
```

### 响应体

```json
{
  "success": true,
  "request_id": "8e0f1a2b-...-c1d2",
  "escalated": false,
  "main_attempts": [
    {
      "channel_id": 1,
      "channel_name": "我的钉钉",
      "channel_type": "dingtalk_bot",
      "success": true,
      "target": null,
      "detail": "钉钉机器人 推送成功",
      "role": "primary",
      "original_channel_id": null,
      "error_kind": "none"
    }
  ],
  "emergency_attempts": [],
  "results": [ ... ],
  "final_channel_id": 1,
  "final_channel_name": "我的钉钉",
  "final_channel_type": "dingtalk_bot",
  "final_role": "primary",
  "total_attempts": 1
}
```

> 如果同类型层级第 1 顺位失败、靠后面的备用渠道成功，`final_role` 会变成 `"backup"`；同类型层级全失败、靠全局紧急层级成功时为 `"emergency"`。调用方只需读 `final_role` + `final_channel_name` 就能知道这次走的是主推送、备用推送还是紧急渠道。

| 字段 | 说明 |
|---|---|
| `success` | 整体是否投递成功 |
| `request_id` | 本次调用的唯一 ID，用于追溯日志 |
| `escalated` | `true` 表示同类型层级全部失败、已自动升级到全局紧急层级 |
| `main_attempts` | 同类型层级（主推送 + 备用）按 priority 升序逐个尝试的记录（任一成功即停止） |
| `emergency_attempts` | 同类型层级全失败后，全局紧急层级并发发送的记录（所有紧急渠道都发，不提前停止；仅升级时非空） |
| `results` | 所有尝试的扁平列表（main + emergency） |
| `final_role` | 最终成功投递的角色：`"primary"`(主推送，第 1 顺位就成功) / `"backup"`(备用推送，前面有失败) / `"emergency"`(紧急渠道，同类型层级全失败)。全失败时为 `null` |
| `final_channel_id` | 最终成功投递的渠道 ID（全失败时为 `null`） |
| `final_channel_name` | 最终成功投递的渠道名称（全失败时为 `null`） |
| `final_channel_type` | 最终成功投递的渠道类型，如 `bark` / `dingtalk_bot`（全失败时为 `null`） |
| `total_attempts` | 本次请求总共尝试的渠道数（含失败 + 成功） |
| `error_kind` | 失败时的错误分类：`rate_limit`(限流) / `auth`(认证) / `config`(配置) / `network`(网络) / `channel_error`(业务错误) |

## 调度策略

外部调用方**必须指定 `channel_type`**（渠道类型），系统按类型调度，分两层依次补位：

1. 找出该类型所有启用的**非紧急**渠道（按 `priority` 升序）组成**同类型层级**（主推送 → 备用1 → 备用2 ...）
2. 按顺位逐个尝试同类型层级：任一成功即停止。第 1 顺位成功为 `primary`，前面有失败靠后面的备用渠道成功为 `backup`
3. 同类型层级全部失败且存在启用的紧急渠道时，自动升级到**全局紧急层级**（不按类型筛选，所有紧急渠道**并发发送**，全部都发不提前停止）。任一紧急渠道成功即整体成功

> **紧急渠道是全局共用的兜底**，不绑定渠道类型——同类型层级是同类型内逐个尝试（主推送 + 备用），全局紧急层级是所有紧急渠道并发发送（不提前停止，确保最大送达率）。每个渠道仅尝试一次（去重），瞬时网络异常（Timeout/ConnectionError）会重试 1 次。所有尝试写入日志，共享同一个 `request_id`。调用方读 `final_role` + `final_channel_name` 即可知道最终走的是主推送、备用推送还是紧急渠道。

## 渠道格式支持矩阵

调用方传 `content_type`（`plain` / `markdown` / `html`），兼容层自动适配：渠道支持就用请求格式，否则降级到该渠道的偏好格式（下表「偏好」列）。各渠道能力基于官方文档核实，文档存放在 `docs/channel-docs/`。

| 渠道类型 | 标签 | 支持格式 | 偏好 | 说明 |
|---|---|---|---|---|
| `bark` | Bark | `plain` / `markdown` | `plain` | markdown 字段由 iOS 客户端渲染，服务端透传 |
| `dingtalk_bot` | 钉钉机器人 | `plain` / `markdown` | `plain` | 钉钉官方支持 markdown msgtype |
| `feishu_bot` | 飞书/Lark 机器人 | `plain` | `plain` | webhook 仅支持 text/post/interactive，不传 markdown |
| `wecom_bot` | 企业微信机器人 | `plain` / `markdown` | `plain` | 企业微信官方支持 markdown msgtype |
| `wecom_app` | 企业微信应用 | `plain` / `markdown` | `plain` | 应用消息接口支持 markdown |
| `telegram_bot` | Telegram Bot | `plain` / `markdown` / `html` | `markdown` | parse_mode: MarkdownV2 / HTML |
| `email` | SMTP 邮件 | `plain` / `html` | `plain` | html 邮件按 html 格式发送 |
| `server_chan` | Server 酱 | `plain` / `markdown` | `markdown` | 官方默认按 markdown 渲染 |
| `pushdeer` | PushDeer | `plain` / `markdown` | `plain` | type=text 或 type=markdown |
| `pushplus` | PushPlus | `plain` / `html` / `markdown` | `html` | template: txt/html/markdown |
| `weplus_bot` | 微加机器人 | `plain` / `html` | `html` | template: txt/html |
| `wxpusher` | WxPusher | `plain` / `html` / `markdown` | `html` | contentType: 1=txt 2=html 3=markdown |
| `gotify` | Gotify | `plain` / `markdown` / `html` | `plain` | extras.client::display.content_type |
| `ntfy` | ntfy | `plain` / `markdown` | `plain` | Markdown: yes 头 |
| `console` | 控制台 | `plain` | `plain` | 调试用 |
| `go_cqhttp` | go-cqhttp | `plain` | `plain` | 仅支持文本消息 |
| `igot` | iGot | `plain` | `plain` | 仅支持文本 |
| `synology_chat` | Synology Chat | `plain` | `plain` | 仅支持文本 |
| `qmsg` | Qmsg 酱 | `plain` | `plain` | 仅支持文本 |
| `aibotk` | 智能微秘书 | `plain` | `plain` | 仅支持文本 |
| `pushme` | PushMe | `plain` | `plain` | 仅支持文本 |
| `chronocat` | Chronocat | `plain` | `plain` | 仅支持文本 |
| `webhook` | 自定义 Webhook | `plain` | `plain` | 由调用方自行处理格式 |

> 调用方也可通过 `GET /admin/api/channel-types` 接口获取每个渠道的 `supported_formats`、`preferred_format` 和 `extra_schema` 字段，用于程序化判断。

## 渠道内容字段（extra）矩阵

> **面向 AI 对接程序的重要说明**：本系统是**个人推送中心**，所有渠道配置的是用户本人的设备/账号。除 `email` 渠道允许在 `target` 参数填第三方收件人外，**其他渠道一律只发送给配置的本人设备/账号**。`extra` 已被白名单限制，不暴露任何收件人/转发字段（Bark 的 `device_key`、PushPlus 的 `to`、ntfy 的 `email` 等均已剥夺），调用方无法通过 `extra` 改变收件目标。以下矩阵列出了每个渠道支持透传的内容字段，**调用方应据此构造 `extra`，不要传矩阵以外的字段**（会被忽略）。程序化获取请调 `GET /admin/api/channel-types`，返回每个渠道的 `extra_schema`。

`/api/notify` 的 `extra` 参数用于透传渠道特有的内容字段。**key 用渠道原生 API 字段名**（非项目自定义命名），与各渠道原生调用机制一致。渠道配置只保留连接凭证，内容字段全部走 `extra`。

> 没有列出 extra 字段的渠道（如钉钉、飞书、企业微信、微加机器人、邮件等）不支持 extra 透传，调用方只需传 `title` / `content` / `content_type`。

### Bark

```json
{"channel_type": "bark", "extra": {"subtitle": "副标题", "group": "分组", "sound": "minuet"}}
```

| extra 字段 | 类型 | 说明 |
|---|---|---|
| `subtitle` | string | 副标题 |
| `group` | string | 分组 |
| `sound` | string | 声音 |
| `icon` | string | 图标 URL |
| `level` | string | 时效等级（active/timeSensitive/passive） |
| `url` | string | 点击跳转 URL |
| `isArchive` | boolean | 是否存档 |
| `badge` | number | 角标数字 |
| `volume` | number | 重要提醒音量 0-10 |
| `autoCopy` | boolean | 自动复制 |
| `copy` | string | 复制内容 |
| `call` | boolean | 重复提醒 |
| `image` | string | 图片 URL |
| `ciphertext` | string | 密文（高级） |
| `action` | string | 操作参数（高级） |
| `id` | string | 消息 ID（高级） |
| `delete` | string | 删除消息 ID（高级） |

### Gotify

```json
{"channel_type": "gotify", "extra": {"priority": 5}}
```

| extra 字段 | 类型 | 说明 |
|---|---|---|
| `priority` | number | 优先级 |
| `extras` | object | extras JSON 对象（高级） |

### PushPlus

```json
{"channel_type": "pushplus", "extra": {"channel": "wechat", "topic": "群组编码"}}
```

| extra 字段 | 类型 | 说明 |
|---|---|---|
| `channel` | string | 渠道（wechat/webhook/cp/mail 等，默认 wechat） |
| `topic` | string | 群组编码 |
| `webhook` | string | Webhook 编码（高级） |
| `callbackUrl` | string | 回调 URL（高级） |

### Telegram Bot

```json
{"channel_type": "telegram_bot", "extra": {"disable_web_page_preview": true, "disable_notification": false}}
```

| extra 字段 | 类型 | 说明 |
|---|---|---|
| `disable_web_page_preview` | boolean | 禁用链接预览 |
| `disable_notification` | boolean | 静默发送 |
| `protect_content` | boolean | 保护内容（高级） |
| `message_thread_id` | number | 话题 ID（高级） |
| `reply_markup` | object | reply_markup JSON（高级） |

### ntfy

```json
{"channel_type": "ntfy", "extra": {"priority": "4", "tags": "warning,server"}}
```

| extra 字段 | 类型 | 说明 |
|---|---|---|
| `priority` | string | 优先级（1-5，默认 3） |
| `tags` | string | 标签，多个用英文逗号分隔 |
| `click` | string | 点击 URL |
| `attach` | string | 附件 URL |
| `filename` | string | 附件文件名 |
| `actions` | string | Actions（高级） |
| `delay` | string | 延迟发送（高级） |


## 错误码

| 状态码 | 含义 |
|---|---|
| `200` | 投递成功（不论主链/备用/紧急哪个命中） |
| `401` | API Key 缺失或错误 |
| `422` | 请求体校验失败（必填缺失 / 多传字段 / 类型错误） |
| `500` | 服务器内部错误 |

> `success=false` 表示所有通道都尝试失败，但 HTTP 状态仍是 200。判断是否成功请看响应体的 `success` 字段。

## 渠道管理

渠道的增删改**只能在 WebUI 进行**，没有对外管理 API。请使用浏览器访问：

```
http://<your-host>:8080/
```

首次访问需输入 API Key 登录，登录后可在「通知配置」页管理渠道，在「系统设置」页修改 API Key。
