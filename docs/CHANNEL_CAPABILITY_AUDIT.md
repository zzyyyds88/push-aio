# Channel Capability Audit

This project started from QingLong's notification script. The goal for API-first
use is stronger than a direct port: callers must be able to use provider-specific
features without changing server code for every new platform option.

## Current Strategy

- Common fields are modeled explicitly in `config_schema`.
- Provider-native payload fields are exposed where the platform supports rich
  message variants.
- `/api/notify` supports `config_overrides`, so API callers can set any channel
  config field per request.

## Completed Deepening

| Channel | Added API-oriented coverage |
| --- | --- |
| Bark | Markdown, subtitle, device_key, device_keys, badge, volume, autoCopy, copy, call, ciphertext, image, action, id, delete |
| Email | Plain/html body, image/file attachments, inline CID images |
| DingTalk | text, markdown, link, actionCard, feedCard, raw payload JSON |
| Feishu/Lark | text, post, interactive card, raw payload JSON |
| WeCom Bot | text, markdown, raw payload JSON for image/news/file/template_card |
| Telegram | parse_mode, link preview, silent send, protected content, topic id, reply_markup |
| Gotify | extras JSON |
| ntfy | tags, click, attach, filename, delay, markdown, email, actions, auth |

## Still Needs Provider-by-Provider Live Validation

These channels are implemented from QingLong behavior but need official-doc
deepening and live-token tests before they can be called complete:

- PushPlus
- PushDeer
- ServerChan
- WxPusher
- Qmsg
- WePlusBot
- Aibotk
- iGot
- PushMe
- Synology Chat
- go-cqhttp
- Chronocat
- WeCom App

For these, the current implementation should send basic messages when configured
correctly, but it may not expose every provider-specific message variant.
