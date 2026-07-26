# Gotify API

> 官方文档：https://gotify.net/docs/
> API 文档（Swagger）：https://gotify.net/api-docs
> 抓取时间：2026-07-26

## 消息模型

A message has the following attributes: content, title, creation date, application id and priority.

## 推送接口

```
POST /message?token=<APP_TOKEN>
Content-Type: application/json
```

## 请求体

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 否 | 消息标题 |
| message | string | 是 | 消息内容 |
| priority | integer | 否 | 优先级（0-10） |
| extras | object | 否 | 扩展字段，用于控制客户端渲染 |

## Markdown 渲染

通过 `extras.client::display.content_type` 指定内容类型，Gotify 客户端会据此渲染：

```json
{
  "title": "测试",
  "message": "## Hello\n\n**Markdown** 内容",
  "priority": 5,
  "extras": {
    "client::display": {
      "content_type": "text/markdown"
    }
  }
}
```

`content_type` 可选值：
- `text/plain`（默认）
- `text/markdown`
- `text/html`

## 关键结论

- Gotify 服务端本身不渲染格式，由**客户端**根据 `extras.client::display.content_type` 渲染
- 设置 `extras.client::display.content_type = "text/markdown"` 后，message 字段会被客户端按 markdown 渲染
- 支持三种内容类型：plain、markdown、html
