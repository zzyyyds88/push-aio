# PushHub · 对接文档

> 本文档面向 **AI Agent / 外部程序**，描述如何对接 PushHub 推送中心。
> 在线版本：服务启动后访问 `http://<your-host>:8080/api/help`。

---

## 一、最小对接三要素

AI 对接 PushHub 只需要三样信息，由部署者提供：

| 要素 | 说明 | 示例 |
|---|---|---|
| **服务 URL** | PushHub 部署地址（固定端口 8080） | `http://192.168.1.10:8080` |
| **channel_type** | 推送渠道类型（告诉 PushHub 发到哪种渠道） | `dingtalk_bot` |
| **X-API-Key** | 鉴权密钥（与 WebUI 登录密码同一把） | `phk_xxxx...` |

> `title` / `content` 是每次调用时由 AI 根据场景生成的消息内容，不属于配置。

### 最小可用请求

```http
POST /api/notify HTTP/1.1
Host: <your-host>:8080
X-API-Key: <你的密钥>
Content-Type: application/json

{"title":"任务完成","content":"已执行完毕","channel_type":"dingtalk_bot"}
```

### 一行 Python 调用

```python
import requests
def push(title, content, channel_type="dingtalk_bot"):
    return requests.post(
        "http://<your-host>:8080/api/notify",
        headers={"X-API-Key": "<你的密钥>"},
        json={"title": title, "content": content, "channel_type": channel_type},
        timeout=15,
    ).json()
```

---

## 二、AI 对接决策流程

```
┌─────────────────────────────────────────────────────────┐
│  1. 向用户索取三要素：URL / channel_type / X-API-Key    │
│  2. （可选）调 GET /admin/api/channel-types 查询渠道能力 │
│  3. 构造请求体：title + content + channel_type           │
│  4. POST /api/notify，读响应                             │
│  5. success=true → 完成；success=false → 报告 request_id │
└─────────────────────────────────────────────────────────┘
```

### 常见 channel_type 速查

| channel_type | 说明 | 支持 markdown |
|---|---|---|
| `dingtalk_bot` | 钉钉群机器人 | ✅ |
| `bark` | Bark（iOS） | ✅ |
| `feishu_bot` | 飞书/Lark 自定义机器人 | ❌ |
| `wecom_bot` / `wecom_app` | 企业微信群机器人 / 应用消息 | ✅ |
| `telegram_bot` | Telegram Bot | ✅ |
| `email` | SMTP 邮件（唯一支持第三方收件人） | ❌（支持 html） |
| `pushplus` / `server_chan` / `pushdeer` / `wxpusher` | 国内微信派推送 | ✅ |
| `gotify` / `ntfy` | 自部署推送服务 | ✅ |

> 完整 23 个渠道列表见 WebUI「新增渠道」页，或调 `GET /admin/api/channel-types` 程序化查询。

---

## 三、接口规范

### 接口概览

| 方法 | 路径 | 鉴权 | 用途 |
|---|---|---|---|
| GET | `/api/health` | 无 | 健康检查 / 监控探活 |
| GET | `/api/help` | 无 | 调用说明页（HTML） |
| GET | `/admin/api/channel-types` | `X-API-Key` | 查询渠道能力（程序化对接用） |
| POST | `/api/notify` | `X-API-Key` | **投递通知（外部程序唯一入口）** |

> 管理接口（渠道增删改、日志查看）只供 WebUI 使用，**不对外公开**。所有配置变更必须登录 WebUI 操作。

### 鉴权

所有需要鉴权的接口都必须在请求头携带：

```
X-API-Key: <你的 API Key>
```

- API Key 与 WebUI 登录密码是**同一把**，保存在数据库的 `settings` 表中。
- 首次启动数据库无 Key 时，需访问 WebUI 完成初始化设置；设置后即可用于登录与外部调用。
- 修改 Key：WebUI「系统设置」页 → 改密码表单，写入 DB 后立即生效、无需重启。
- 未携带或携带错误返回 `401 Unauthorized`：

```json
{"detail": "无效或缺失的 API Key。请在请求头携带 X-API-Key。"}
```

### 投递通知 · 请求

```
POST /api/notify
Content-Type: application/json
X-API-Key: <你的 API Key>
```

**请求体（严格模式 `extra="forbid"`）**

> 多传任何字段都会被拒绝（422），防止外部调用方绕过系统调度策略。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `title` | string | 是 | 通知标题，1-255 字符 |
| `content` | string | 是 | 通知正文 |
| `channel_type` | string | 是 | **必填**：渠道类型（如 `bark` / `dingtalk_bot` / `feishu_bot`）。系统在该类型的启用非紧急渠道里按 priority 逐个尝试（主推送 → 备用1 → 备用2 ...），全失败再升级到全局紧急层级（并发发送） |
| `content_type` | string | 否 | `plain`(默认) / `markdown` / `html` |
| `attachments` | array | 否 | 附件列表（目前仅 email 渠道支持） |
| `extra` | object | 否 | 渠道特有的内容字段，透传给渠道。key 用渠道**原生 API 字段名**。详见下方[渠道内容字段（extra）矩阵](#五渠道内容字段extra矩阵) |

> **`channel_type` 是必填字段**：本系统是按类型调度的推送中心，不存在"全局主推送渠道"概念——调用方必须明确要发到哪种渠道。外部程序只需告诉 PushHub "我要发到钉钉"，不需知道具体渠道 ID。
>
> **`extra` 不影响调度策略**，仅透传给渠道用于构造 payload。渠道配置（DB）只保留连接凭证（token、url 等），内容字段全部通过 `extra` 按消息传递，与各渠道原生调用机制一致。

### 投递通知 · 响应

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

> **`final_role` 是 AI 判断结果的最简字段**：
> - `"primary"` → 主推送成功，链路正常
> - `"backup"` → 主推送失败、靠备用渠道成功，可提醒用户检查主渠道
> - `"emergency"` → 同类型层级全失败、靠紧急渠道兜底，应提醒用户检查该类型所有渠道
> - `null` → 全部失败，AI 应把 `request_id` 报告给用户供排查
>
> 错误分类不在顶层响应字段中，而是在每条尝试记录里：`results[].error_kind` / `main_attempts[].error_kind` / `emergency_attempts[].error_kind`，取值为 `rate_limit`(限流) / `auth`(认证) / `config`(配置) / `network`(网络) / `channel_error`(业务错误) / `none`(未分类)。

### 错误码

| 状态码 | 含义 | AI 处理建议 |
|---|---|---|
| `200` | 投递完成（不论主/备用/紧急哪个命中） | 看 `success` 字段判断结果 |
| `401` | API Key 缺失或错误 | 立即停止，提示用户检查 Key |
| `422` | 请求体校验失败（必填缺失 / 多传字段 / 类型错误） | 修正请求体，不要重试 |
| `500` | 服务器内部错误 | 指数退避重试 2-3 次 |

> `success=false` 表示所有通道都尝试失败，但 HTTP 状态仍是 200。判断是否成功请看响应体的 `success` 字段。

---

## 四、调度策略（AI 无需干预）

外部调用方**必须指定 `channel_type`**，系统按类型调度，分两层依次补位：

1. **同类型层级**：找出该类型所有启用的**非紧急**渠道（按 `priority` 升序）组成顺序链（主推送 → 备用1 → 备用2 ...），按顺位逐个尝试，**任一成功即停止**。
2. **全局紧急层级**：同类型层级全部失败且存在启用的紧急渠道时，自动升级。**所有紧急渠道并发发送**（不提前停止），任一成功即整体成功。

```
同类型层级（按顺序逐个尝试）
    钉钉主推送 → 钉钉备用1 → 钉钉备用2 → ... → 全部失败
        ↓ 自动升级
全局紧急层级（所有紧急渠道并发）
    邮件 + Bark + ...  同时发送
```

- 同一次请求内**每个通道最多尝试一次**（去重），避免环路。
- 瞬时网络异常（Timeout / ConnectionError）会重试 1 次。
- 所有尝试写入日志，共享同一个 `request_id`，标记 `role` 和 `error_kind`。

> **AI 不需要也无法干预调度**：不允许传 `channel_ids`、`priority`、`force_emergency` 等字段（严格模式直接 422）。AI 只负责传 `channel_type` + 消息内容，切换决策完全由系统内部固定执行。

---

## 五、渠道内容字段（extra）矩阵

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

---

## 六、渠道格式支持矩阵

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

---

## 七、调用示例

### curl

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"任务完成","content":"已执行完毕","channel_type":"dingtalk_bot"}'
```

### Markdown 内容

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"构建报告","content":"## 详情\n- 成功 12\n- 失败 0","content_type":"markdown","channel_type":"dingtalk_bot"}'
```

### 指定渠道类型 + extra 透传（Bark 带副标题和声音）

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"报警","content":"CPU 超过 90%","channel_type":"bark","extra":{"subtitle":"服务器告警","sound":"alarm","group":"监控"}}'
```

### PowerShell

```powershell
Invoke-WebRequest -Uri http://<your-host>:8080/api/notify `
  -Method POST `
  -Headers @{ "X-API-Key" = "<你的 key>" } `
  -ContentType "application/json" `
  -Body '{"title":"任务完成","content":"已执行完毕","channel_type":"dingtalk_bot"}'
```

### Python（requests）

```python
import requests

resp = requests.post(
    "http://<your-host>:8080/api/notify",
    headers={"X-API-Key": "<你的 key>"},
    json={"title": "任务完成", "content": "已执行完毕", "channel_type": "dingtalk_bot"},
)
print(resp.json())
```

---

## 八、AI 对接最佳实践

- **超时设置**：单次 `/api/notify` 调用建议 `timeout=15` 秒。系统内部已对每个渠道做 15 秒超时控制 + 1 次网络重试，调用方不需要自己实现重试。
- **不要重试 422**：请求体校验失败（多传字段 / 缺必填 / 类型错误）是程序 bug，重试不会成功。修正请求体即可。
- **401 立即停止**：API Key 错误，重试无意义。提示用户检查 Key。
- **5xx 可重试**：服务器内部错误，可指数退避重试 2-3 次。
- **`success=false` 不要盲目重试**：所有渠道都已尝试过，重试只会再次走完同一条链路。若需提高送达率，应让用户在 WebUI 增加更多备用 / 紧急渠道，而不是调用方重试。
- **批量推送节流**：高频率推送应在调用方做本地队列 + 节流，避免触发各渠道限流（如钉钉每机器人每分钟 20 条）。
- **`final_role` 是最简判断字段**：`primary` 链路正常，`backup` 提醒用户主渠道异常，`emergency` 提醒用户该类型全部异常，`null` 报告 `request_id` 给用户排查。

---

## 九、渠道管理

渠道的增删改**只能在 WebUI 进行**，没有对外管理 API。请使用浏览器访问：

```
http://<your-host>:8080/
```

首次访问需输入 API Key 登录，登录后可在「新增渠道」/「渠道管理」页管理渠道，在「系统设置」页修改 API Key。
