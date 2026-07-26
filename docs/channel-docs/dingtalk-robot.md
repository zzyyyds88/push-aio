服务端 API即时通信IM机器人消息发送与接收类型

# 消息发送与接收类型

更新于 2026-05-15本文介绍了通过机器人发送消息的类型与数据格式，并详细介绍了机器人接收消息的数据格式。

## 机器人发送消息

### 消息类型

发送机器人消息的方式有2种，通过**接口发送** 机器人消息和通过**Webhook发送** 机器人消息。不同的方式，支持的消息类型和数据格式不同。

**说明**

推荐使用接口方式发送消息。

| 消息类型 | 接口方式发送机器人消息 | Webbook方式发送机器人消息 |
|---|---|---|
| Text文本类型 | ✅ | ✅ |
| Markdown类型 | ✅ | ✅ |
| 图片Image类型 | ✅ | ❌ |
| ActionCard类型 | ✅ | ✅ |
| FeedCard类型 | ❌ | ✅ |
| Link链接消息 | ✅ | ✅ |
| Audio语音类型 | ✅ | ❌ |
| File文件类型 | ✅ | ❌ |
| Video视频类型 | ✅ | ❌ |

如果上述消息类型均无法满足你的要求，可以使用[互动卡片](https://open.dingtalk.com/document/development/overview-card#)。

### 方式一：接口方式

**重要**

- 人与机器人会话中机器人消息：支持图片、语音、文件**收发** 能力。

- 群聊会话中机器人消息：图片、语音、视频、文件**发送** 能力，**但群聊中用户无法@机器人发送语音、视频、文件给机器人** 。

#### 适用接口

- [批量发送人与机器人会话中机器人消息](https://open.dingtalk.com/document/development/chatbots-send-one-on-one-chat-messages-in-batches#)

- [机器人发送群聊消息](https://open.dingtalk.com/document/development/the-robot-sends-a-group-message#)

#### 数据格式

- **消息模板Key** ：消息模板Key是开发者发送消息时需要用到的一个唯一标识。它可以在编写程序代码时，能快速地指向一个事先设定好的消息模板。

- **消息模板参数** ：用于在消息模板中替换预定义占位符的实际数据。例如，当你有一个`sampleText`消息模板Key时，此时你需要定义`content`字段的值。

- **示例** ：提供了企业内部应用机器人在**群内** 发送**文本类型** 的 HTTP 示例代码：

    - 消息模板Key： ` "msgKey" : "sampleText"`

    - 消息模板参数：` "msgParam" : "{\"content\":\"钉钉，让进步发生\"}"`

详情参考[机器人发送群聊消息](https://open.dingtalk.com/document/development/the-robot-sends-a-group-message#)。

| 消息类型 | 消息模板Key | 消息模板参数 | 说明 |
|---|---|---|---|
| 文本类型 | sampleText | Loading... | ![](https://aka.doubaocdn.com/s/Dsdc1wqMoC) |
| Markdown类型 | sampleMarkdown | Loading... | ![](https://aka.doubaocdn.com/s/WbMB1wqMoC) |
| 图片类型 | sampleImageMsg | Loading... | ![](https://aka.doubaocdn.com/s/U4Rz1wqMoC)
**说明**
photoURL可填写图片的完整URL路径，也可填写图片的mediaId。mediaId可通过[上传媒体文件](https://open.dingtalk.com/document/development/upload-media-files#)接口，获取`media_id`参数值。 |
| 链接类型 | sampleLink | Loading... | 链接消息。 |
| ActionCard类型  | sampleActionCard | Loading... | 卡片消息：一个按钮。
![](https://aka.doubaocdn.com/s/cvB31wqMoC) |
| sampleActionCard2 | Loading... | 卡片消息：竖向二个按钮。
![](https://aka.doubaocdn.com/s/5PrY1wqMoC) | |
| sampleActionCard3 | Loading... | 卡片消息：竖向三个按钮。 | |
| sampleActionCard4 | Loading... | 卡片消息：竖向四个按钮。 | |
| sampleActionCard5 | Loading... | 卡片消息：竖向五个按钮。 | |
| sampleActionCard6 | Loading... | 卡片消息：横向二个按钮。
![](https://aka.doubaocdn.com/s/OGS11wqMoC) | |
| 语音类型 | sampleAudio | Loading... | 语音消息：
**mediaId** ：通过[上传媒体文件](https://open.dingtalk.com/document/development/upload-media-files#)接口，获取`media_id`参数值。
**说明**
支持ogg、amr格式。
**duration** ：语音消息时长，单位毫秒。
![](https://aka.doubaocdn.com/s/o7nr1wqMoC) |
| 文件类型 | sampleFile | Loading... | 文件消息：
**mediaId** ：通过[上传媒体文件](https://open.dingtalk.com/document/development/upload-media-files#)接口，获取`media_id`参数值。
**fileName** ：文件名称。
**fileType** ：文件类型。
**说明**
文件类型，支持xlsx、pdf、zip、rar、doc、docx格式。
![](https://aka.doubaocdn.com/s/U7Vc1wqMoC) |
| 视频类型 | sampleVideo | Loading... | 视频消息：
**duration** ：语音消息时长，单位秒。
**videoMediaId** ：通过[上传媒体文件](https://open.dingtalk.com/document/development/upload-media-files#)接口，获取`media_id`参数值。
**videoType** ：视频类型，支持mp4格式。
**picMediaId** ：视频封面图，通过[上传媒体文件](https://open.dingtalk.com/document/development/upload-media-files#)接口，获取`media_id`参数值。
**height** ：视频展示高度，单位px。
**width** ：视频展示宽度，单位px。 |

#### Markdown支持的语法

对于消息类型 sampleMarkdown 的markdown语法的补充说明。

### 方式二：Webhook方式

**说明**

webhook方式只支持在群聊会话。

Webhook发送消息的实现方式，请参考[机器人回复/发送消息](https://open.dingtalk.com/document/dingstart/robot-reply-and-send-messages#)和[创建自定义机器人](https://open.dingtalk.com/document/dingstart/custom-bot-creation-and-installation#)。

#### 文本text类型

| **参数** | **是否必填** | **类型** | **说明** |
|---|---|---|---|
| msgtype | 是 | String | text。 |
| content | 是 | String | 消息文本。 |
| atMobiles | 否 | Array | 被@人的手机号。
**说明**
在content里添加@人的手机号，且只有在群内的成员才可被@，非群内成员手机号会被脱敏。 |
| atUserIds | 否 | Array | 被@人的用户userid。
**说明**
在content里添加@人的userId。 |
| isAtAll | 否 | Boolean | @所有人是true，否则为false。 |

![](https://aka.doubaocdn.com/s/hFEe1wqMoC)

#### 链接Link类型

**说明**

该类型不支持@人。

| **参数** | **参数类型** | 是否必填 | **说明** |
|---|---|---|---|
| msgtype | String | 是 | 消息类型，此时固定为：link。 |
| title | String | 是 | 消息标题。 |
| text | String | 是 | 消息内容，如果太长只会部分展示。 |
| messageUrl | String | 是 | 点击消息跳转的URL，打开方式如下：
移动端，在钉钉客户端内打开
PC端
默认侧边栏打开
希望在外部浏览器打开，参考[消息链接说明](https://open.dingtalk.com/document/development/message-link-description#)。 |
| picUrl | String | 否 | 图片URL。 |

![](https://aka.doubaocdn.com/s/2fMQ1wqMoC)

#### Markdown类型

| **参数** | **是否必填** | **类型** | **说明** |
|---|---|---|---|
| msgtype | 是 | String | 消息类型，此时固定为：markdown。 |
| title | 是 | String | 首屏会话透出的展示内容。 |
| text | 是 | String | Markdown格式的消息内容。 |
| atMobiles | 否 | Array | 被@人的手机号。
**说明**
在text内容里要有@人的手机号，只有在群内的成员才可被@，非群内成员手机号会被脱敏。 |
| atUserIds | 否 | Array | 被@人的用户userid。
**说明**
在 text 中添加@人的userId。 |
| isAtAll | 否 | Boolean | @所有人是true，否则为false。 |

![](https://aka.doubaocdn.com/s/RMP31wqMoC)

目前只支持Markdown语法的子集，支持的元素如下：

#### ActionCard类型

- **整体跳转ActionCard类型**

| **参数** | **是否必填** | **类型** | **说明** |
|---|---|---|---|
| msgtype | 是 | String | 消息类型，此时固定为：actionCard。 |
| title | 是 | String | 首屏会话透出的展示内容。 |
| text | 是 | String | markdown格式的消息。
**说明**
如果需要实现 @ 功能 ，在 text 内容中添加 @ 用户的 userId。例如：@manager7675 |
| singleTitle | 是 | String | 单个按钮的标题。 |
| singleURL | 是 | String | 点击消息跳转的URL，打开方式如下：
移动端，在钉钉客户端内打开
PC端
默认侧边栏打开
希望在外部浏览器打开，参考[消息链接说明](https://open.dingtalk.com/document/development/message-link-description#)。 |
| btnOrientation | 否 | String | 按钮排列方式：
**0** ：按钮竖直排列
**1** ：按钮横向排列 |

![](https://aka.doubaocdn.com/s/U5Hz1wqMoC)

- **独立跳转ActionCard类型**

| **参数** | **是否必填** | **类型** | **说明** |
|---|---|---|---|
| msgtype | 是 | String | actionCard。 |
| title | 是 | String | 首屏会话透出的展示内容。 |
| text | 是 | String | markdown格式的消息内容。
**说明**
如果需要实现 @ 功能 ，在 text 内容中添加 @ 用户的 userId。例如：@manager7675 |
| btns | 是 | Array | 按钮。 |
| title | 是 | String | 按钮标题。 |
| actionURL | 是 | String | 击按钮触发的URL，打开方式如下：
移动端，在钉钉客户端内打开
PC端
默认侧边栏打开
希望在外部浏览器打开，参考[消息链接说明](https://open.dingtalk.com/document/development/message-link-description#)。 |
| btnOrientation | 否 | String | 按钮排列顺序。
**0** ：按钮竖直排列
**1** ：按钮横向排列 |

![](https://aka.doubaocdn.com/s/VheO1wqMoC)

#### FeedCard类型

**说明**

该类型不支持@人。

| **参数** | **是否必填** | **类型** | **说明** |
|---|---|---|---|
| msgtype | 是 | String | feedCard。 |
| title | 是 | String | 单条信息文本。 |
| messageURL | 是 | String | 点击单条信息到跳转链接，详情参考[消息链接说明](https://open.dingtalk.com/document/development/message-link-description#)。 |
| picURL | 是 | String | 单条信息后面图片的URL。 |

![](https://aka.doubaocdn.com/s/ybVc1wqMoC)

当不想回复消息到群里时，回复格式如下：

## 机器人接收消息

当用户@群机器人或与机器人发送单聊消息时，钉钉会把机器人接收到的消息发送到开发者设置的机器人回调服务。

### 消息体

本示例以 text 文本类型为例：如果你使用 HTTP 回调的方式，使用 POST 请求接收钉钉推送的消息。

| **参数** | **类型** | **说明** |
|---|---|---|
| senderPlatform | String | 消息发送平台。 |
| conversationId | String | 会话ID。 |
| atUsers | Array of Object | 被@人的信息。
**dingtalkId** ：加密的被@用户的id。
**staffId** ：被@用户的userId，外部群中的外部用户此字段为空。
**unionId** ：被@的用户unionid。 |
| chatbotCorpId | String | 加密的机器人所在的企业corpId。 |
| chatbotUserId | String | 加密的机器人ID。 |
| msgId | String | 加密的消息ID。 |
| senderNick | String | 发送者昵称。 |
| isAdmin | Boolean | 是否为管理员：
true：是
false：否
机器人发布上线后生效，否则不返回。 |
| senderStaffId | String | 企业内部群中@该机器人的成员 userId。
如果发送人非机器人所在企业成员，则此字段为空（比如外部群里外部成员@机器人的情况）。
机器人发布上线后生效。否则不会返回。 |
| senderUnionId | String | 发送人的unionid。 |
| sessionWebhookExpiredTime | Long | 当前会话的Webhook地址过期时间。 |
| createAt | String | 消息的时间戳，单位毫秒。 |
| senderCorpId | String | 企业内部群的发送者当前群的企业corpId。 |
| conversationType | String | 会话类型：
**1** ：单聊
**2** ：群聊 |
| senderId | String | 加密的发送者ID。 |
| conversationTitle | String | 群聊时才有的会话标题。 |
| isInAtList | Boolean | 是否在@列表中。 |
| sessionWebhook | String | 当前会话的Webhook地址。 |
| text | Object | 消息文本：
content：机器人接收的消息内容。
该字段仅在消息类型为 text 存在。 |
| msgtype | String | 消息类型：
text：文本消息
richText：富文本消息
picture：图片消息
audio：语音消息
video：视频消息
file：文件消息
消息类型的具体格式参看下方**消息类型** 。 |
| robotCode | String | 机器人编码。
自定义机器人无 robotCode。 |

### 消息类型

机器人目前支持接收文本、语音、图片、文件、视频、富文本类型消息，下方为机器人接收各种消息类型的字段解释。除消息类型和消息体字段不同之外，其余参数字段与上面表格相同。

#### 文本消息

| **参数** | **类型** | **说明** |
|---|---|---|
| msgtype | String | 消息类型：
**text** ：文本消息 |
| text | Object | 消息文本：
**content** ：机器人接收的消息内容。 |

#### 富文本消息

| 名称 | 类型 | 描述 |
|---|---|---|
| msgtype | String | 消息类型：
**richText** ：富文本 |
| content | Object | 消息内容。 |
| richText | Array of Object | 富文本列表。
**说明**
消息列表中可以包含：
**text：** 文本消息
**picture** ：图片消息
图片文件的下载码downloadCode，可通过调用服务端API-[下载机器人接收消息的文件内容](https://open.dingtalk.com/document/development/download-the-file-content-of-the-robot-receiving-message#)接口获取临时下载链接。 |

#### 图片消息

| **参数** | **类型** | **说明** |
|---|---|---|
| msgtype | String | 消息类型：
**picture** ：图片消息 |
| downloadCode | String | 图片文件的下载码，用于换取下载图片的二进制文件，可通过调用服务端API-[下载机器人接收消息的文件内容](https://open.dingtalk.com/document/development/download-the-file-content-of-the-robot-receiving-message#)接口获取临时下载链接。 |

#### 语音消息

**说明**

群聊会话中，群成员 @机器人时，机器人**不支持** 接收语音消息。

| **参数** | **类型** | **说明** |
|---|---|---|
| msgtype | String | 消息类型：
**audio** ：语音消息 |
| downloadCode | String | 语音文件的下载码，用于换取下载语音的二进制文件，可通过调用服务端API-[下载机器人接收消息的文件内容](https://open.dingtalk.com/document/development/download-the-file-content-of-the-robot-receiving-message#)口获取临时下载链接。 |
| recognition | String | 语音识别后的文本。 |
| duration | Long | 语音的时长，单位是毫秒。 |

#### 视频消息

**说明**

群聊会话中，群成员 @机器人时，机器人**不支持** 接收视频消息。

| **参数** | **类型** | **说明** |
|---|---|---|
| msgtype | String | 消息类型：
**video** ：视频消息 |
| downloadCode | String | 视频文件的下载码，用于换取下载视频的二进制文件，可通过调用服务端API-[下载机器人接收消息的文件内容](https://open.dingtalk.com/document/development/download-the-file-content-of-the-robot-receiving-message#)接口获取临时下载链接。 |
| videoType | String | 视频文件类型。 |
| duration | Long | 视频的时长，单位是毫秒。 |

#### 文件消息

**说明**

群聊会话中，群成员 @机器人时，机器人**不支持** 接收文件消息。

| **参数** | **类型** | **说明** |
|---|---|---|
| msgtype | String | 消息类型：
**video** ：文件消息 |
| downloadCode | String | 文件的下载码，用于换取下载文件的二进制文件，可通过调用服务端API-[下载机器人接收消息的文件内容](https://open.dingtalk.com/document/development/download-the-file-content-of-the-robot-receiving-message#)接口获取临时下载链接。 |
| fileName | String | 文件名。 |

### 相关内容

如果[创建企业内部应用机器人](https://open.dingtalk.com/document/dingstart/configure-the-robot-application#)时，消息接收模式选择了 HTTP模式，在机器人使用过程中，当机器人收到消息时，此时除了上述的消息体，此时还存在 HTTP header参数，格式如下：

| **参数** | **说明** |
|---|---|
| timestamp | 消息发送的时间戳，单位是毫秒。 |
| sign | 签名值。 |

你需要对 header 中的 timestamp 和 sign 进行验证，用来判断是否是来自钉钉的合法请求，避免其他仿冒钉钉调用开发者的HTTPS服务传送数据，具体验证逻辑如下：

- timestamp 与系统当前时间戳如果相差1小时以上，则认为是非法的请求。

- sign 与开发者自己计算的结果不一致，则认为是非法的请求。

当timestamp和sign同时验证通过，才能认为是来自钉钉的合法请求。

使用HmacSHA256算法计算签名，然后进行Base64 encode，得到最终的签名值，示例如下：

| **配置项** | **说明** |
|---|---|
| timestamp | 当前时间的时间戳，单位毫秒 |
| appSecret | 应用的 Client Secret，详情参考[Client Secret](https://open.dingtalk.com/document/dingstart/basic-concepts-beta#section-pje-9wf-l7c)。 |

### 错误码

当机器人 Webhook 和 Stream 用量超量后，则会出现以下内容：

#### 错误表现

##### 群聊会话

