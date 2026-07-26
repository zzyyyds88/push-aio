# push-aio · 外部调用说明

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

API Key 与 WebUI 登录密码是**同一把**，来源于服务器 `.env` 文件中的 `PUSH_AIO_API_KEY`。未配置则服务拒绝启动。

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

### 调用示例

**curl**

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"任务完成","content":"已执行完毕"}'
```

**Markdown 内容**

```bash
curl -X POST http://<your-host>:8080/api/notify \
  -H "X-API-Key: <你的 key>" \
  -H "Content-Type: application/json" \
  -d '{"title":"构建报告","content":"## 详情\n- 成功 12\n- 失败 0","content_type":"markdown"}'
```

**PowerShell**

```powershell
Invoke-WebRequest -Uri http://<your-host>:8080/api/notify `
  -Method POST `
  -Headers @{ "X-API-Key" = "<你的 key>" } `
  -ContentType "application/json" `
  -Body '{"title":"任务完成","content":"已执行完毕"}'
```

**Python（requests）**

```python
import requests

resp = requests.post(
    "http://<your-host>:8080/api/notify",
    headers={"X-API-Key": "<你的 key>"},
    json={"title": "任务完成", "content": "已执行完毕"},
)
print(resp.json())
```

### 响应体

```json
{
  "success": true,
  "request_id": "8e0f1a2b-...-c1d2",
  "escalated": false,
  "chains": [
    {
      "primary": {
        "channel_id": 1,
        "channel_name": "我的 Bark",
        "channel_type": "bark",
        "success": true,
        "target": null,
        "detail": "OK",
        "role": "primary",
        "original_channel_id": null
      },
      "backups": [],
      "success": true,
      "final_role": "primary"
    }
  ],
  "emergency_attempts": [],
  "results": [ ... ]
}
```

| 字段 | 说明 |
|---|---|
| `success` | 整体是否投递成功 |
| `request_id` | 本次调用的唯一 ID，用于追溯日志 |
| `escalated` | `true` 表示主链全部失败、已自动升级到紧急通道 |
| `chains` | 每个主通道一条链路（含主尝试 + 备用尝试） |
| `emergency_attempts` | 紧急通道尝试记录（仅升级时非空） |
| `results` | 所有尝试的扁平列表 |

## 调度策略

外部调用方**无法选择渠道、无法指定优先级**，系统统一执行：

1. 找出所有启用的**非紧急**通道（按 `priority` 升序）作为主通道
2. 对每个主通道尝试发送：
   - 主通道本身失败时，按其 `backup_channel_ids` 顺序逐个尝试备用通道
   - 任一备用成功即停止该链路
3. 所有主链全部失败且存在启用的紧急通道时，自动升级，逐个尝试紧急通道

> 同一次请求内每个通道最多尝试一次（去重），瞬时网络异常会重试 1 次。所有尝试写入日志，共享同一个 `request_id`。

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
