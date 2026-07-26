# 渠道错误码与限流规则参考

本文档基于各渠道官方文档核对整理，**修改 `services/channels.py` 的 `errcode_map` 前请先核对本文档**，避免改回错误的码值。

核对时间：2026-07-26

---

## 错误分类（ErrorKind）

`services/channels.py` 中 `ErrorKind` 定义：

| error_kind | 含义 | dispatcher 决策 |
|---|---|---|
| `none` | 成功 | 不触发切换 |
| `rate_limit` | 被限流 | 不重试，立即切备用 |
| `auth` | 认证失败（token 错/过期/无权限） | 不重试，立即切备用 |
| `config` | 配置错误（缺必填/格式错/参数错） | 不重试，立即切备用（需用户改配置） |
| `network` | 网络异常（Timeout/ConnectionError/5xx） | 重试 1 次后切备用 |
| `channel_error` | 渠道业务错误（余额不足/用户不存在/内容违规等） | 不重试，立即切备用 |

### 通用识别规则（`classify_response`）

| HTTP 状态码 | error_kind |
|---|---|
| 429 | `rate_limit` |
| 401 / 403 | `auth` |
| 400 | `config` |
| 5xx | `network` |
| 其他 | 走 body 关键字匹配（`classify_text`），都不命中则 `channel_error` |

---

## 钉钉群机器人（dingtalk_bot）

**官方文档**：https://open.dingtalk.com/document/orgapp/custom-robots-send-group-messages

**限流规则**：每个机器人每分钟最多 20 条，超限限流 10 分钟

### errcode_map

| errcode | error_kind | 说明 |
|---|---|---|
| 410100 | rate_limit | **发送速度太快而限流**（真正的限流码） |
| 90030 | rate_limit | webhook 调用次数达到上限（每日上限） |
| 400101 | auth | access_token 不存在 |
| 88 | auth | access_token is blank |
| 310000 | config | 安全校验失败：关键词未匹配 / 签名不匹配 / IP不在白名单 / timestamp无效 |
| 400102 | channel_error | 机器人已停用 |
| 400013 | channel_error | 群已被解散 |

### 历史误录（已删除，勿改回）

- ~~130101 / 130102~~：官方文档中不存在，是虚构码
- ~~88 = rate_limit~~：实际是 access_token 为空，应归 auth
- ~~310000 = auth~~：实际是安全校验失败，应归 config

---

## 飞书/Lark 自定义机器人（feishu_bot）

**官方文档**：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot

**限流规则**：单租户单机器人 100 次/分钟 + 5 次/秒（双限制）

**重要**：webhook 机器人与 Open API 错误码完全不同。`9999166x` 是 Open API 码，webhook 机器人不返回。

### errcode_map（注意字段是 `code` 不是 `errcode`）

| code | error_kind | 说明 |
|---|---|---|
| 11232 | rate_limit | create message service trigger rate limit |
| 11247 | rate_limit | internal send message trigger rate limit |
| 19021 | auth | 签名不匹配 |
| 19022 | auth | IP 不在白名单 |
| 19024 | auth | 关键词未匹配 |
| 9499 | config | 请求体格式错误（Bad Request） |

### 历史误录（已删除，勿改回）

- ~~130102~~：钉钉风格码，飞书中不存在
- ~~99991663 / 99991664 / 99991661 / 99991668~~：Open API 码，webhook 机器人不返回

---

## 企业微信群机器人（wecom_bot）

**官方文档**：https://developer.work.weixin.qq.com/document/path/90313

**限流规则**：每个 webhook 地址每分钟最多 20 条

### errcode_map

| errcode | error_kind | 说明 |
|---|---|---|
| 45009 | rate_limit | 接口调用超过限制 |
| 45033 | rate_limit | 接口并发调用超过限制 |
| 42001 | auth | access_token 已过期 |
| 40014 | auth | 不合法的 access_token |
| 41001 | config | 缺少 access_token 参数 |
| 41004 | config | 缺少 secret 参数 |

### 历史误录（已删除，勿改回）

- ~~45100 / 93000 / 93001~~：官方文档中不存在，是虚构码
- ~~41001 / 41004 = auth~~：官方含义是"缺少参数"，应归 config

---

## 企业微信应用消息（wecom_app）

**官方文档**：https://developer.work.weixin.qq.com/document/path/90313

### errcode_map

| errcode | error_kind | 说明 |
|---|---|---|
| 45009 | rate_limit | 接口调用超过限制 |
| 45033 | rate_limit | 接口并发调用超过限制 |
| 42001 | auth | access_token 已过期 |
| 40014 | auth | 不合法的 access_token |
| 41001 | config | 缺少 access_token 参数 |

---

## Telegram Bot（telegram_bot）

**官方文档**：https://core.telegram.org/bots/api#response-errors

**限流规则**：单 bot 单 chat，按消息类型有 1 秒 1 条 / 30 秒 20 条等限制

**注意**：`error_code` 字段与 HTTP 状态码同值。429 时返回 `parameters.retry_after`（秒），当前实现选择立即切备用（不等待），符合个人推送中心低延迟诉求。

### errcode_map（用 `error_code` 字段）

| error_code | error_kind | 说明 |
|---|---|---|
| 429 | rate_limit | Too Many Requests |
| 401 | auth | Unauthorized，token 无效 |
| 403 | auth | Forbidden（被封禁/chat不存在等） |

---

## PushPlus（pushplus）

**官方文档**：https://www.pushplus.plus/doc/guide/code.html

**限流规则**：非会员每日 1000 次，触发 900 后账号级封禁 2~7 天

### errcode_map（用 `code` 字段）

| code | error_kind | 说明 |
|---|---|---|
| 401 | auth | 请求未授权（开放接口未启用） |
| 403 | auth | 请求 IP 未授权 |
| 500 | network | 系统异常（可重试） |
| 600 | channel_error | 数据异常 |
| 888 | channel_error | 积分不足 |
| 900 | rate_limit | 用户账号使用受限（请求次数过多） |
| 903 | auth | 无效的用户令牌 |
| 905 | config | 账户未实名认证 |
| 999 | channel_error | 服务端验证错误 |

### 历史误录（已删除，勿改回）

- ~~901 / 902~~：官方文档中不存在，是幽灵码

---

## WxPusher（wxpusher）

**官方文档**：https://wxpusher.zjiecode.com/

### errcode_map（用 `code` 字段，1000 = 成功）

| code | error_kind | 说明 |
|---|---|---|
| 1001 | auth | appToken 无效或缺失 |
| 1002 | config | content 为空 |
| 1003 | config | 无有效 UID/TopicId |
| 1004 | auth | 应用不存在 |
| 1005 | channel_error | 服务器内部错误 |

---

## Bark（bark）

**官方文档**：https://bark.day.app/ 、bark-server 源码 `util/response.go`

**限流规则**：官方 `api.day.app` 无明确 QPS 限制；自部署由前置 nginx 决定

**实现说明**：无 `errcode_map`，靠 HTTP 状态码识别。bark-server 成功返回 `{"code": 200}`，失败时 body `code` 与 HTTP status 一致。自部署 nginx 429 限流时返回 HTML（非 JSON），落到 `classify_text` 关键字匹配能正确识别。

---

## ntfy（ntfy）

**官方文档**：https://docs.ntfy.sh/publish/

**限流规则**：ntfy.sh 公共实例每 visitor 250 条/天

**实现说明**：无 `errcode_map`，ntfy 不返回业务 code，只用 HTTP 状态码。429 时响应头含 `Retry-After`，当前实现选择立即切备用（不等待）。

---

## 未映射 errcode_map 的渠道

以下渠道依赖通用 `classify_response`（HTTP 状态码 + body 关键字）识别，功能上能识别 429/401/403/400/5xx，但无法区分细分业务错误：

| 渠道 | 备注 |
|---|---|
| Server 酱 | 返回 `errno` 字段，限流时 errmsg 含"今日额度已用完" |
| PushDeer | 返回 `code` 字段，官方未列出错误码表 |
| Gotify / IGot / Qmsg / PushMe / 微加机器人 / 智能微秘书 / go-cqhttp / Chronocat / Synology Chat | 靠 HTTP 状态码识别 |
| 自定义 Webhook | 靠 HTTP 状态码识别 |
| SMTP 邮件 | 用 smtplib 异常分类：SMTPAuthenticationError→auth、SMTPConnectError/SMTPServerDisconnected→network、SMTPResponseException 4xx→rate_limit/5xx→channel_error |
| 控制台 | 始终成功 |

---

## 修改 errcode_map 时的检查清单

1. 先核对本文档中对应渠道的表格
2. 如有疑问，访问对应官方文档链接（已附在每节标题下方）
3. 修改后在本文档同步更新
4. 注意区分 webhook 机器人与 Open API 的错误码（飞书的 9999166x 是典型坑）
5. 不要凭记忆添加错误码，必须以官方文档为准
