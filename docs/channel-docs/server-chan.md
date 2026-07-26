# Server酱（ServerChan·Turbo）

> 官方文档：https://sct.ftqq.com/sendkey
> 抓取时间：2026-07-26

## 接口

```
POST https://sctapi.ftqq.com/<SENDKEY>.send
```

## 请求体（form/json 均可）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 消息标题（最长 32 字符，不展示换行） |
| desp | string | 否 | 消息内容，**支持 Markdown 语法** |
| channel | string | 否 | 指定推送渠道，不传则走默认 |
| openid | string | 否 | 指定接收人 openid |

## 关键结论

- **`desp` 字段天生支持 Markdown 渲染**，微信端会以富文本展示
- 不传 `desp` 时只推标题
- 免费版每日限额 5 条，付费版额度更高

## 示例

```bash
curl "https://sctapi.ftqq.com/<SENDKEY>.send" \
  -X POST \
  -d "title=测试标题&desp=## 这是一条测试\n\n**Markdown** 内容"
```
