[ 发送应用消息 ](https://developer.work.weixin.qq.com/document/path/90236)

企业内部开发

服务端API

消息接收与发送

发送应用消息

 发送应用消息  

最后更新：2025/09/24

目录

[接口定义](https://developer.work.weixin.qq.com/document/path/90236#%E6%8E%A5%E5%8F%A3%E5%AE%9A%E4%B9%89)[消息类型](https://developer.work.weixin.qq.com/document/path/90236#%E6%B6%88%E6%81%AF%E7%B1%BB%E5%9E%8B) [文本消息](https://developer.work.weixin.qq.com/document/path/90236#%E6%96%87%E6%9C%AC%E6%B6%88%E6%81%AF) [图片消息](https://developer.work.weixin.qq.com/document/path/90236#%E5%9B%BE%E7%89%87%E6%B6%88%E6%81%AF) [语音消息](https://developer.work.weixin.qq.com/document/path/90236#%E8%AF%AD%E9%9F%B3%E6%B6%88%E6%81%AF) [视频消息](https://developer.work.weixin.qq.com/document/path/90236#%E8%A7%86%E9%A2%91%E6%B6%88%E6%81%AF) [文件消息](https://developer.work.weixin.qq.com/document/path/90236#%E6%96%87%E4%BB%B6%E6%B6%88%E6%81%AF) [文本卡片消息](https://developer.work.weixin.qq.com/document/path/90236#%E6%96%87%E6%9C%AC%E5%8D%A1%E7%89%87%E6%B6%88%E6%81%AF) [图文消息](https://developer.work.weixin.qq.com/document/path/90236#%E5%9B%BE%E6%96%87%E6%B6%88%E6%81%AF) [图文消息（mpnews）](https://developer.work.weixin.qq.com/document/path/90236#%E5%9B%BE%E6%96%87%E6%B6%88%E6%81%AF%EF%BC%88mpnews%EF%BC%89) [markdown消息](https://developer.work.weixin.qq.com/document/path/90236#markdown%E6%B6%88%E6%81%AF) [小程序通知消息](https://developer.work.weixin.qq.com/document/path/90236#%E5%B0%8F%E7%A8%8B%E5%BA%8F%E9%80%9A%E7%9F%A5%E6%B6%88%E6%81%AF) [模板卡片消息](https://developer.work.weixin.qq.com/document/path/90236#%E6%A8%A1%E6%9D%BF%E5%8D%A1%E7%89%87%E6%B6%88%E6%81%AF) [文本通知型](https://developer.work.weixin.qq.com/document/path/90236#%E6%96%87%E6%9C%AC%E9%80%9A%E7%9F%A5%E5%9E%8B) [图文展示型](https://developer.work.weixin.qq.com/document/path/90236#%E5%9B%BE%E6%96%87%E5%B1%95%E7%A4%BA%E5%9E%8B) [按钮交互型](https://developer.work.weixin.qq.com/document/path/90236#%E6%8C%89%E9%92%AE%E4%BA%A4%E4%BA%92%E5%9E%8B) [投票选择型](https://developer.work.weixin.qq.com/document/path/90236#%E6%8A%95%E7%A5%A8%E9%80%89%E6%8B%A9%E5%9E%8B) [多项选择型](https://developer.work.weixin.qq.com/document/path/90236#%E5%A4%9A%E9%A1%B9%E9%80%89%E6%8B%A9%E5%9E%8B)[附录](https://developer.work.weixin.qq.com/document/path/90236#%E9%99%84%E5%BD%95) [支持的markdown语法](https://developer.work.weixin.qq.com/document/path/90236#%E6%94%AF%E6%8C%81%E7%9A%84markdown%E8%AF%AD%E6%B3%95) [id转译说明](https://developer.work.weixin.qq.com/document/path/90236#id%E8%BD%AC%E8%AF%91%E8%AF%B4%E6%98%8E)

## 接口定义

应用支持推送文本、图片、视频、文件、图文等类型。

**请求方式：** POST（**HTTPS** ）

**请求地址：**  https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=ACCESS_TOKEN

**参数说明：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| access_token | 是 | 调用接口凭证 |

\- 各个消息类型的具体POST格式请阅后续“消息类型”部分。

\- 如果有在管理端对应用设置“在微工作台中始终进入主页”，应用在微信端只能接收到文本消息，并且文本消息的长度限制为20字节，超过20字节会被截断。同时其他消息类型也会转换为文本消息，提示用户到企业微信查看。

\- 支持id转译，将userid/部门id转成对应的用户名/部门名，在企业授权了会话内容存档接口权限时，也可以将消息id和群id转成对应的消息内容/群名称，目前仅**文本/文本卡片/图文/图文（mpnews）/任务卡片/小程序通知/模版消息/模板卡片消息** 这八种消息类型的**部分字段** 支持。具体支持的范围和语法，请查看附录[id转译说明](https://developer.work.weixin.qq.com/document/path/90236#10167/id%E8%BD%AC%E8%AF%91%E8%AF%B4%E6%98%8E)。

\- 支持重复消息检查，当指定 `"enable_duplicate_check": 1`开启: 表示在一定时间间隔内，同样内容（请求json）的消息，不会重复收到；时间间隔可通过`duplicate_check_interval`指定，默认`1800秒`。

\- 从2021年2月4日开始，企业关联添加的「小程序」应用，也可以发送文本、图片、视频、文件、图文等各种类型的消息了。

**调用建议** ：大部分企业应用在每小时的0分或30分触发推送消息，容易造成资源挤占，从而投递不够及时，建议尽量避开这两个时间点进行调用。

**频率限制** ：每应用不可超过账号上限数\*200人次/天（注：若调用api一次发给1000人，算1000人次；若企业账号上限是500人，则每个应用每天可发送100000人次的消息）。每应用对同一个成员不可超过30次/分钟，1000次/小时，超过部分会被丢弃不下发

**返回示例：**

```
{   "errcode" : 0,   "errmsg" : "ok",   "invaliduser" : "userid1|userid2",   "invalidparty" : "partyid1|partyid2",   "invalidtag": "tagid1|tagid2",   "unlicenseduser" : "userid3|userid4",   "msgid": "xxxx",   "response_code": "xyzxyz" }
```
如果部分接收人无权限或不存在，发送仍然执行，但会返回无效的部分（即invaliduser或invalidparty或invalidtag或unlicenseduser），常见的原因是**接收人不在应用的可见范围内** 。

权限包含**应用可见范围** 和**基础接口权限** (基础账号、互通账号均可)，unlicenseduser中的用户在应用可见范围内但没有基础接口权限。

如果**全部** 接收人无权限或不存在，则本次调用返回失败，errcode为81013。

返回包中的userid，不区分大小写，统一转为小写

**参数说明：**

| 参数 | 说明 |
|---|---|
| errcode | 返回码 |
| errmsg | 对返回码的文本描述内容 |
| invaliduser | 不合法的userid，不区分大小写，统一转为小写 |
| invalidparty | 不合法的partyid |
| invalidtag | 不合法的标签id |
| unlicenseduser | 没有基础接口许可(包含已过期)的userid |
| msgid | 消息id，用于[撤回应用消息](https://developer.work.weixin.qq.com/document/path/90236#31947) |
| response_code | 仅消息类型为“按钮交互型”，“投票选择型”和“多项选择型”，以及填写了action_menu字段的文本通知型、图文展示型的模板卡片消息返回，应用可使用response_code调用[更新模版卡片消息](https://developer.work.weixin.qq.com/document/path/90236#32086)接口，72小时内有效，且只能使用一次 |

## 消息类型

### 文本消息

**请求示例：**

```
{    "touser" : "UserID1|UserID2|UserID3",    "toparty" : "PartyID1|PartyID2",    "totag" : "TagID1 | TagID2",    "msgtype" : "text",    "agentid" : 1,    "text" : {        "content" : "你的快递已到，请携带工卡前往邮件中心领取。\n出发前可查看<a href=\"https://work.weixin.qq.com\">邮件中心视频实况</a>，聪明避开排队。"    },    "safe":0,    "enable_id_trans": 0,    "enable_duplicate_check": 0,    "duplicate_check_interval": 1800 }
```
**参数说明：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| touser | 否 | 指定接收消息的成员，成员ID列表（多个接收者用‘\|’分隔，最多支持1000个）。
特殊情况：指定为"@all"，则向该企业应用的全部成员发送 |
| toparty | 否 | 指定接收消息的部门，部门ID列表，多个接收者用‘\|’分隔，最多支持100个。
当touser为"@all"时忽略本参数 |
| totag | 否 | 指定接收消息的标签，标签ID列表，多个接收者用‘\|’分隔，最多支持100个。
当touser为"@all"时忽略本参数 |
| msgtype | 是 | 消息类型，此时固定为：text |
| agentid | 是 | 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 [获取企业授权信息](https://developer.work.weixin.qq.com/document/path/90236#10975/%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E6%8E%88%E6%9D%83%E4%BF%A1%E6%81%AF) 获取该参数值 |
| content | 是 | 消息内容，最长不超过2048个字节，超过将截断**（支持id转译）** |
| safe | 否 | 表示是否是保密消息，0表示可对外分享，1表示不能分享且内容显示水印，默认为0 |
| enable_id_trans | 否 | 表示是否开启id转译，0表示否，1表示是，默认0。 |
| enable_duplicate_check | 否 | 表示是否开启重复消息检查，0表示否，1表示是，默认0 |
| duplicate_check_interval | 否 | 表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时 |

touser、toparty、totag不能同时为空，后面不再强调。

**文本消息展现：**

![](https://aka.doubaocdn.com/s/fJqb1wqMkg)

**特殊说明：**

其中text参数的content字段可以支持换行、以及A标签，即可打开自定义的网页（可参考以上示例代码）(注意：换行符请用转义过的\n)

### 图片消息

**请求示例：**

```
{    "touser" : "UserID1|UserID2|UserID3",    "toparty" : "PartyID1|PartyID2",    "totag" : "TagID1 | TagID2",    "msgtype" : "image",    "agentid" : 1,    "image" : {         "media_id" : "MEDIA_ID"    },    "safe":0,    "enable_duplicate_check": 0,    "duplicate_check_interval": 1800 }
```
**请求参数：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| touser | 否 | 成员ID列表（消息接收者，多个接收者用‘\|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送 |
| toparty | 否 | 部门ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| totag | 否 | 标签ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| msgtype | 是 | 消息类型，此时固定为：image |
| agentid | 是 | 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 [获取企业授权信息](https://developer.work.weixin.qq.com/document/path/90236#10975/%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E6%8E%88%E6%9D%83%E4%BF%A1%E6%81%AF) 获取该参数值 |
| media_id | 是 | 图片媒体文件id，可以调用上传临时素材接口获取 |
| safe | 否 | 表示是否是保密消息，0表示可对外分享，1表示不能分享且内容显示水印，默认为0 |
| enable_duplicate_check | 否 | 表示是否开启重复消息检查，0表示否，1表示是，默认0 |
| duplicate_check_interval | 否 | 表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时 |

### 语音消息

**请求示例：**

```
{    "touser" : "UserID1|UserID2|UserID3",    "toparty" : "PartyID1|PartyID2",    "totag" : "TagID1 | TagID2",    "msgtype" : "voice",    "agentid" : 1,    "voice" : {         "media_id" : "MEDIA_ID"    },    "enable_duplicate_check": 0,    "duplicate_check_interval": 1800 }
```
**参数说明：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| touser | 否 | 成员ID列表（消息接收者，多个接收者用‘\|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送 |
| toparty | 否 | 部门ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| totag | 否 | 标签ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| msgtype | 是 | 消息类型，此时固定为：voice |
| agentid | 是 | 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 [获取企业授权信息](https://developer.work.weixin.qq.com/document/path/90236#10975/%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E6%8E%88%E6%9D%83%E4%BF%A1%E6%81%AF) 获取该参数值 |
| media_id | 是 | 语音文件id，可以调用[上传临时素材](https://developer.work.weixin.qq.com/document/path/90236#10112)接口获取 |
| enable_duplicate_check | 否 | 表示是否开启重复消息检查，0表示否，1表示是，默认0 |
| duplicate_check_interval | 否 | 表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时 |

### 视频消息

**请求示例：**

```
{    "touser" : "UserID1|UserID2|UserID3",    "toparty" : "PartyID1|PartyID2",    "totag" : "TagID1 | TagID2",    "msgtype" : "video",    "agentid" : 1,    "video" : {         "media_id" : "MEDIA_ID",         "title" : "Title",        "description" : "Description"    },    "safe":0,    "enable_duplicate_check": 0,    "duplicate_check_interval": 1800 }
```
**参数说明：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| touser | 否 | 成员ID列表（消息接收者，多个接收者用‘\|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送 |
| toparty | 否 | 部门ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| totag | 否 | 标签ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| msgtype | 是 | 消息类型，此时固定为：video |
| agentid | 是 | 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 [获取企业授权信息](https://developer.work.weixin.qq.com/document/path/90236#10975/%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E6%8E%88%E6%9D%83%E4%BF%A1%E6%81%AF) 获取该参数值 |
| media_id | 是 | 视频媒体文件id，可以调用[上传临时素材](https://developer.work.weixin.qq.com/document/path/90236#10112)接口获取 |
| title | 否 | 视频消息的标题，不超过128个字节，超过会自动截断 |
| description | 否 | 视频消息的描述，不超过512个字节，超过会自动截断 |
| safe | 否 | 表示是否是保密消息，0表示可对外分享，1表示不能分享且内容显示水印，默认为0 |
| enable_duplicate_check | 否 | 表示是否开启重复消息检查，0表示否，1表示是，默认0 |
| duplicate_check_interval | 否 | 表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时 |

**视频消息展现：**

![](https://aka.doubaocdn.com/s/O2l91wqMkg)

### 文件消息

**请求示例：**

```
{    "touser" : "UserID1|UserID2|UserID3",    "toparty" : "PartyID1|PartyID2",    "totag" : "TagID1 | TagID2",    "msgtype" : "file",    "agentid" : 1,    "file" : {         "media_id" : "1Yv-zXfHjSjU-7LH-GwtYqDGS-zz6w22KmWAT5COgP7o"    },    "safe":0,    "enable_duplicate_check": 0,    "duplicate_check_interval": 1800 }
```
**参数说明：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| touser | 否 | 成员ID列表（消息接收者，多个接收者用‘\|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送 |
| toparty | 否 | 部门ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| totag | 否 | 标签ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| msgtype | 是 | 消息类型，此时固定为：file |
| agentid | 是 | 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 [获取企业授权信息](https://developer.work.weixin.qq.com/document/path/90236#10975/%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E6%8E%88%E6%9D%83%E4%BF%A1%E6%81%AF) 获取该参数值 |
| media_id | 是 | 文件id，可以调用上传临时素材接口获取 |
| safe | 否 | 表示是否是保密消息，0表示可对外分享，1表示不能分享且内容显示水印，默认为0，保密消息支持以下格式文件： txt、pdf、doc、docx、ppt、pptx、xls、xlsx、xml、jpg、jpeg、png、bmp、gif |
| enable_duplicate_check | 否 | 表示是否开启重复消息检查，0表示否，1表示是，默认0 |
| duplicate_check_interval | 否 | 表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时 |

**文件消息展现：**

![](https://aka.doubaocdn.com/s/1JeZ1wqMkg)

### 文本卡片消息

**请求示例：**

```
{    "touser" : "UserID1|UserID2|UserID3",    "toparty" : "PartyID1 | PartyID2",    "totag" : "TagID1 | TagID2",    "msgtype" : "textcard",    "agentid" : 1,    "textcard" : {             "title" : "领奖通知",             "description" : "<div class=\"gray\">2016年9月26日</div> <div class=\"normal\">恭喜你抽中iPhone 7一台，领奖码：xxxx</div><div class=\"highlight\">请于2016年10月10日前联系行政同事领取</div>",             "url" : "URL",                         "btntxt":"更多"    },    "enable_id_trans": 0,    "enable_duplicate_check": 0,    "duplicate_check_interval": 1800 }
```
**参数说明：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| touser | 否 | 成员ID列表（消息接收者，多个接收者用‘\|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送 |
| toparty | 否 | 部门ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| totag | 否 | 标签ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| msgtype | 是 | 消息类型，此时固定为：textcard |
| agentid | 是 | 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 [获取企业授权信息](https://developer.work.weixin.qq.com/document/path/90236#10975/%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E6%8E%88%E6%9D%83%E4%BF%A1%E6%81%AF) 获取该参数值 |
| title | 是 | 标题，不超过128个字符，超过会自动截断**（支持id转译）** |
| description | 是 | 描述，不超过512个字符，超过会自动截断**（支持id转译）** |
| url | 是 | 点击后跳转的链接。最长2048字节，请确保包含了协议头(http/https) |
| btntxt | 否 | 按钮文字。 默认为“详情”， 不超过4个文字，超过自动截断。 |
| enable_id_trans | 否 | 表示是否开启id转译，0表示否，1表示是，默认0 |
| enable_duplicate_check | 否 | 表示是否开启重复消息检查，0表示否，1表示是，默认0 |
| duplicate_check_interval | 否 | 表示是否重复消息检查的时间间隔，默认1800s，最大不超过4小时 |

**文本卡片消息展现 ：**

![](https://aka.doubaocdn.com/s/jdoQ1wqMkg)

**特殊说明** ：

卡片消息的展现形式非常灵活，支持使用br标签或者空格来进行换行处理，也支持使用div标签来使用不同的字体颜色，目前内置了3种文字颜色：灰色(gray)、高亮(highlight)、默认黑色(normal)，将其作为div标签的class属性即可，具体用法请参考上面的示例。

### 图文消息

**请求示例：**

```
{    "touser" : "UserID1|UserID2|UserID3",    "toparty" : "PartyID1 | PartyID2",    "totag" : "TagID1 | TagID2",    "msgtype" : "news",    "agentid" : 1,    "news" : {        "articles" : [            {                "title" : "中秋节礼品领取",                "description" : "今年中秋节公司有豪礼相送",                "url" : "URL",                "picurl" : "https://res.mail.qq.com/node/ww/wwopenmng/images/independent/doc/test_pic_msg1.png",  			 "appid": "wx123123123123123",         	   "pagepath": "pages/index?userid=zhangsan&orderid=123123123"            }         ]    },    "enable_id_trans": 0,    "enable_duplicate_check": 0,    "duplicate_check_interval": 1800 }
```
**参数说明：**

| 参数 | 是否必须 | 说明 |
|---|---|---|
| touser | 否 | 成员ID列表（消息接收者，多个接收者用‘\|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送 |
| toparty | 否 | 部门ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| totag | 否 | 标签ID列表，多个接收者用‘\|’分隔，最多支持100个。当touser为@all时忽略本参数 |
| msgtype | 是 | 消息类型，此时固定为：news |
| agentid | 是 | 企业应用的id，整型。企业内部开发，可在应用的设置页面查看；第三方服务商，可通过接口 [获取企业授权信息](https://developer.work.weixin.qq.com/document/path/90236#10975/%E8%8E%B7%E5%8F%96%E4%BC%81%E4%B8%9A%E6%8E%88%E6%9D%83%E4%BF%A1%E6%81%AF) 获取该参数值 |
| articles | 是 | 图文消息，一个图文消息支持1到8条图文 |
| title | 是 | 标题，不超过128个字节，超过会自动截断**（支持id转译）** |
| description | 否 | 描述，不超过512个字节，超过会自动截断**（支持id转译）** |
| url | 否 | 点击后跳转的链接。 最长2048字节，请确保包含了协议头(http/https)，小程序或者url必须填写一个 |
| picurl | 否 | 图文消息的图片链接，最长2048字节，支持JPG、PNG格式，较好的效果为大图 1068\*455，小图150\*150。 |
| appid | 否 | 小程序appid，必须是与当前应用关联的小程序，appid和pagepath必须同时填写，填写后会忽略url字段 |
| pagepath | 否 | 点击消息卡片后的小程序页面，最长128字节，仅限本小程序内的页面。appid和pagepath必须同时填写，填写后会忽略url字段 |
| enable_id_trans | 否 | 表示是否开启id转译，0表示否，1表示是，默认0 |
| enable_duplicate_check | 否 | 表示是否开启重复消息检查，0表示否，1表示是，默认0 |
