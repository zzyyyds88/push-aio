# PushHub 设计文档

> 本文档是项目的核心设计基线,所有 WebUI、API、dispatcher 实现都必须遵循此文档。
> 代码实现与文档冲突时,以本文档为准;修改代码需同步更新本文档。

---

# 第一部分:外部调用方需知

> 这一节面向**调用 `/api/notify` 的外部程序开发者**。看完这一部分就足够集成。

## 1.1 PushHub 是什么

PushHub 是一个**多渠道推送中心**:把钉钉、Bark、飞书、邮件等多种推送渠道集中托管,外部程序通过统一的 HTTP API 调用,不必每个程序自己对接各家 SDK。

- 你只需要告诉 PushHub「发到哪种渠道」(如钉钉),具体走哪条 token、失败后怎么切换,由 PushHub 内部处理
- 所有渠道都是用户自己在 WebUI 上配置的,为本地用户自己的设备服务

## 1.2 调用 `/api/notify`

**请求**

```
POST /api/notify
Header: X-API-Key: <你的 Key>
Content-Type: application/json
```

**请求体字段**

| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| `channel_type` | 是 | string | 渠道类型,如 `dingtalk_bot`、`bark`、`feishu_bot`、`email` 等 |
| `title` | 是 | string | 推送标题(1-255 字符) |
| `content` | 是 | string | 推送内容 |
| `content_type` | 否 | string | 内容格式:`plain`(默认)/`markdown`/`html` |
| `attachments` | 否 | array | 附件列表,目前仅邮件渠道支持 |
| `extra` | 否 | object | 渠道原生内容字段透传,见 1.4 |

**严格模式**:传任何未声明字段(如 `channel_ids`、`priority`、`force_emergency`)一律返回 422。外部调用方**不能**干预调度顺序。

## 1.3 响应

```json
{
  "success": true,
  "request_id": "uuid",
  "final_role": "primary",
  "final_channel_id": 1,
  "final_channel_name": "主推送渠道",
  "final_channel_type": "dingtalk_bot",
  "total_attempts": 1,
  "main_attempts": [...],
  "emergency_attempts": [],
  "escalated": false,
  "results": [...]
}
```

| 字段 | 说明 |
|------|------|
| `success` | 整体是否成功 |
| `final_role` | 最终投递角色:`primary`(主推送)/`backup`(备用)/`emergency`(紧急)/`null`(全失败) |
| `final_channel_*` | 最终投递的渠道信息,全失败时为 `null` |
| `total_attempts` | 本次请求尝试的渠道总数 |
| `main_attempts` | 同类型层级尝试记录(按顺序) |
| `emergency_attempts` | 全局紧急层级尝试记录(并发) |
| `escalated` | 是否触发了紧急升级 |

## 1.4 `extra` 透传

渠道的**连接凭证**(token、URL、签名密钥)由用户在 WebUI 配置,不在调用参数里。**内容相关字段**通过 `extra` 透传给渠道原生 API。

- `extra` 的 key 用**渠道原生 API 字段名**(如 Bark 的 `subtitle`、`sound`,钉钉的 `at`),不是项目自定义命名
- 各渠道支持的 `extra` 字段可通过 `GET /admin/api/channel-types` 查询

## 1.5 查询渠道能力

```
GET /admin/api/channel-types
Header: X-API-Key: <你的 Key>
```

返回每个渠道类型的能力声明:`supported_formats`(支持的 content_type)、`preferred_format`(降级偏好)、`extra_schema`(支持的 extra 字段)。调用方据此判断能否用 markdown/html 推送、能传哪些 extra 字段。

---

# 第二部分:内部设计

> 这一节面向**项目维护者**,讲调度逻辑、错误处理、WebUI 呈现等实现细节。

## 2.1 调度的两层结构

PushHub 的调度分**两个独立层次**,依次补位:

```
第一层:同类型层级(按顺序依次补位)
    钉钉主推送 → 钉钉备用1 → 钉钉备用2 → ... → 全部失败
        ↓ 全部失败时升级
第二层:全局紧急层级(所有紧急渠道并发)
    所有类型的紧急渠道一起并发发送
```

### 第一层:同类型层级

同一种 `channel_type` 下,启用的非紧急渠道按 `priority` 升序排列,形成依次补位的顺序链:

- 第 1 顺位:**主推送渠道**(`final_role = primary`)
- 第 2 顺位:**备用推送渠道 1**(`final_role = backup`)
- 第 3 顺位:**备用推送渠道 2**(`final_role = backup`)
- ... 更多备用渠道依次补位
- 按顺位逐个尝试,**任一成功即停止**
- 全部顺位都失败时,升级到第二层

以钉钉为例,若配置了主推送、备用1、备用2 三个渠道,发送顺序为:主推送 → 备用1 → 备用2,三个都失败才升级到全局紧急层。

### 第二层:全局紧急层级

- 与 `channel_type` **无关**,所有类型的紧急渠道一起参与
- 触发时**全部并发发送**(不提前停止),任一成功即整体成功
- `final_role = emergency`
- 用途:作为最后兜底(如邮件、短信等可达性强的渠道)

## 2.2 紧急升级触发条件

只有满足**两个条件**才触发紧急升级:
1. 第一层(同类型层级)的渠道**全部失败**
2. 至少存在 1 个启用的紧急渠道

紧急渠道**不参与同类型层级的顺序排序**——它只属于全局紧急层级。

## 2.3 错误分类(ErrorKind)

每个渠道发送结果带 `error_kind` 字段,dispatcher 据此决定是否切换:

| ErrorKind | 含义 | 切换策略 |
|-----------|------|----------|
| `none` | 成功 | — |
| `rate_limit` | 限流(HTTP 429 / 钉钉 410100 等) | 立即切下一个 |
| `auth` | 认证失败(token 错 / 401 / 403) | 立即切下一个 |
| `config` | 配置错误(缺必填 / 格式错) | 立即切下一个(需用户改配置) |
| `network` | 网络异常(Timeout / ConnectionError) | **重试 1 次**后再切 |
| `channel_error` | 渠道业务错误(余额不足 / 用户不存在等) | 立即切下一个 |

### 重试策略

- **网络异常**(Timeout / ConnectionError / ChunkedEncodingError):重试 1 次,仍失败则切下一个渠道
- **其他错误**:不重试,直接返回让 dispatcher 切换
- 重试只针对单渠道内的瞬时网络问题,不与层级切换冲突

## 2.4 格式兼容层

外部调用方传 `content_type`(plain/markdown/html),dispatcher 通过兼容层适配渠道能力:

| 函数 | 位置 | 作用 |
|------|------|------|
| `resolve_format` | `services/format_adapter.py` | 决策最终格式:渠道支持就用请求格式,否则降级到 `preferred_format` |
| `convert_content` | `services/format_adapter.py` | 转换 content 到最终格式(如 markdown→plain 降级) |

每个渠道类声明两个类属性:
- `supported_formats`:支持的 content_type 列表(基于 `docs/channel-docs/` 下的官方文档核实)
- `preferred_format`:请求格式不支持时的降级偏好(如 PushPlus 偏好 html、Server 酱偏好 markdown)

## 2.5 渠道管理 WebUI 呈现

渠道管理页按三个分区展示:

### 同类型层级分组
- 每个 `channel_type` 一个分组(如「钉钉机器人」「Bark」)
- 组内按 `priority` 升序:第 1 个标「主推送」,第 2 个起标「备用 N」
- 组内支持拖拽 / 上移下移调整顺序
- 每个分组右上角有「添加」按钮,点击后打开新增抽屉并预选该类型

### 全局紧急层级分组
- 所有 `is_emergency=True` 的启用渠道,与类型无关
- 每条标「紧急」「并发」标签
- 底部提示「紧急渠道不参与顺位排序,触发时全部并发发送」

### 已禁用渠道
- 不参与任何推送链路
- 提供「启用」按钮可重新加入

### 「新增渠道」按钮位置
- **topbar 全局按钮**:仅在渠道管理页显示,其他页面隐藏(通过路由切换 `hidden` 属性)
- **分组内按钮**:每个渠道类型分组右上角,预选该类型

## 2.6 新建渠道的默认归属

- 新建渠道默认 `is_emergency=False`,加入所在类型组末尾
- `priority` 自动追加:取**同 `is_emergency` 值**的启用渠道 `max(priority) + 10`(跨 channel_type 共享 priority 空间,因为同类型内才按 priority 比较,跨类型 priority 值不冲突)
- 顺序调整完全由 WebUI「上移/下移」按钮或拖拽负责,用户无需手填 priority
- 需要作为紧急渠道时,通过渠道卡片上的「改为紧急通道」按钮切换 `is_emergency`

## 2.7 三种测试发送路径

| 路径 | 用途 | 是否走调度 | 是否写库/写日志 |
|------|------|-----------|-----------------|
| `POST /admin/api/channels/{id}/test` | 单渠道测试 | 否,只发指定渠道 | 写日志,角色 `primary` |
| `POST /admin/api/channels/probe` | 保存前预检 | 否,用表单配置直接发 | 不写库、不写日志 |
| `POST /admin/api/notify` | WebUI 完整调度测试 | 是,与外部调用相同流程 | 写日志 |

WebUI 完整调度测试可选传 `channel_ids` 限定测试范围,空则走全自动调度。

## 2.8 代码对应关系

| 设计概念 | 代码位置 |
|----------|----------|
| 必填 `channel_type` | `schemas.py` `NotifyRequest.channel_type` |
| 严格模式 `extra="forbid"` | `schemas.py` `NotifyRequest.model_config` |
| 同类型层级按 priority 逐个尝试 | `services/dispatcher.py` `dispatch` 主备用循环 |
| 全局紧急层级并发 | `services/dispatcher.py` `dispatch` 紧急层级 `ThreadPoolExecutor` |
| 紧急渠道不按类型筛选 | `services/dispatcher.py` `emergency_query`(无 `Channel.type` 过滤) |
| `is_emergency` 标记 | `models.py` `Channel.is_emergency` |
| `priority` 排序 | `models.py` `Channel.priority` |
| 上移/下移调整 | `api/routes.py` `POST /admin/api/channels/{id}/move` |
| `final_role` 标签 | `schemas.py` `NotifyResponse.final_role` |
| 错误分类 ErrorKind | `services/channels.py` `ErrorKind` |
| 1+1 网络重试 | `services/dispatcher.py` `_send_one` |
| 格式兼容层 | `services/format_adapter.py` `resolve_format`/`convert_content` |
| 渠道格式能力声明 | `services/channels.py` 各 Sender 类 `supported_formats`/`preferred_format` |
| extra 透传 | `services/dispatcher.py` `_send_one` 传 `payload.extra` |
| 单渠道测试 | `services/dispatcher.py` `dispatch_single` |
| 保存前 probe | `services/dispatcher.py` `probe_channel` |
| WebUI 完整测试 | `api/routes.py` `POST /admin/api/notify`(`AdminNotifyRequest`) |
