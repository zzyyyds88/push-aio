# Bark Server API V2

> 来源：https://raw.githubusercontent.com/Finb/bark-server/master/docs/API_V2.md
> 抓取时间：2026-07-26

## Push

| Field | Type | Description |
| ----- | ---- | ----------- |
| title (optional) | string | Notification title (font size would be larger than the body) |
| subtitle (optional) | string | Notification subtitle |
| body  | string | Notification content |
| device_key | string | The key for each device |
| device_keys (optional) | array | Used for batch pushing |
| level (optional) | string | `'critical'`, `'active'`, `'timeSensitive'`, `'passive'` |
| volume (optional) | string | The ringtone volume for critical alert notification. |
| badge (optional) | integer | The number displayed next to App icon |
| call (optional) | string | Must be `1`, The ringtone will continue to play for 30 seconds |
| autoCopy (optional) | string | Must be `1` |
| copy (optional) | string |  The value to be copied |
| sound (optional) | string | Value from [Sounds](https://github.com/Finb/Bark/tree/master/Sounds)， and custom ringtones are also available |
| icon (optional) | string | An url to the icon, available only on iOS 15 or later |
| group (optional) | string | The group of the notification |
| ciphertext (optional) | string | The ciphertext of encrypted push notifications |
| isArchive (optional) | string | Value must be `1`. Whether or not should be archived by the app |
| ttl (optional) | integer | Time to live for archived messages, in seconds. Expired archived messages are deleted automatically |
| url (optional) | string | Url that will jump when click notification |
| action (optional) | string | Set to "none", tap notifications do nothing |

### curl 示例

```sh
curl -X "POST" "http://127.0.0.1:8080/push" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "body": "Test Bark Server",
  "device_key": "ynJ5Ft4atkMkWeo2PAvFhF",
  "title": "bleem",
  "badge": 1,
  "sound": "minuet",
  "icon": "https://day.app/assets/images/avatar.jpg",
  "group": "test",
  "url": "https://mritd.com"
}'
```

## 关键结论

- **bark-server 官方 API V2 的 Push 接口字段中没有 `markdown` 字段**
- `markdown` 字段是 Bark iOS APP 客户端的自定义渲染扩展（在 [Finb/Bark](https://github.com/Finb/Bark) APP 端实现），不是 bark-server 后端 API 的标准字段
- 服务端会透传未知字段给 APNs，iOS APP 客户端识别 `markdown` 字段后用 MarkdownView 渲染
- 因此：依赖 Bark iOS APP 客户端版本，服务端 API 本身不感知 markdown 语义

## Misc

- `GET /ping` - 探活
- `GET /healthz` - 健康检查
- `GET /info` - 服务器信息
