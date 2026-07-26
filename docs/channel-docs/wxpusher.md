# [WxPusher消息推送平台](https://wxpusher.zjiecode.com/)

- [介绍](https://wxpusher.zjiecode.com/docs/#/?id=%e4%bb%8b%e7%bb%8d)

    - [什么是WxPusher](https://wxpusher.zjiecode.com/docs/#/?id=%e4%bb%80%e4%b9%88%e6%98%afwxpusher)

    - [demo演示程序](https://wxpusher.zjiecode.com/docs/#/?id=demo%e6%bc%94%e7%a4%ba%e7%a8%8b%e5%ba%8f)

    - [APP效果预览](https://wxpusher.zjiecode.com/docs/#/?id=app%e6%95%88%e6%9e%9c%e9%a2%84%e8%a7%88)

    - [微信ClawBot效果预览](https://wxpusher.zjiecode.com/docs/#/?id=%e5%be%ae%e4%bf%a1clawbot%e6%95%88%e6%9e%9c%e9%a2%84%e8%a7%88)

- [消息接收通道](https://wxpusher.zjiecode.com/docs/#/?id=%e6%b6%88%e6%81%af%e6%8e%a5%e6%94%b6%e9%80%9a%e9%81%93)

    - [全平台下载](https://wxpusher.zjiecode.com/docs/#/?id=app-download)

    - [iOS苹果客户端](https://wxpusher.zjiecode.com/docs/#/?id=ios%e8%8b%b9%e6%9e%9c%e5%ae%a2%e6%88%b7%e7%ab%af)

    - [Android客户端](https://wxpusher.zjiecode.com/docs/#/?id=android%e5%ae%a2%e6%88%b7%e7%ab%af)

        - [应用下载](https://wxpusher.zjiecode.com/docs/#/?id=%e5%ba%94%e7%94%a8%e4%b8%8b%e8%bd%bd)

        - [当前厂商适配情况](https://wxpusher.zjiecode.com/docs/#/?id=%e5%bd%93%e5%89%8d%e5%8e%82%e5%95%86%e9%80%82%e9%85%8d%e6%83%85%e5%86%b5)

- [2种发送方式](https://wxpusher.zjiecode.com/docs/#/?id=_2%e7%a7%8d%e5%8f%91%e9%80%81%e6%96%b9%e5%bc%8f)

- [方式一：标准推送](https://wxpusher.zjiecode.com/docs/#/?id=standard)

        - [发送消息](https://wxpusher.zjiecode.com/docs/#/?id=%e5%8f%91%e9%80%81%e6%b6%88%e6%81%af)

# [介绍](https://wxpusher.zjiecode.com/docs/#/?id=%e4%bb%8b%e7%bb%8d)

本文档由 WxPusher 官方维护，最后更新：2026-07-11。接口字段、限制和线上行为以本文档为准。

## [什么是WxPusher](https://wxpusher.zjiecode.com/docs/#/?id=%e4%bb%80%e4%b9%88%e6%98%afwxpusher)

[**WxPusher消息推送平台** ](https://wxpusher.zjiecode.com/) 是四川思明今创科技有限公司旗下的一套实时消息推送服务平台：早期以微信公众号为主要触达通道，**当前主推独立全平台客户端接收** （各安卓厂商推送、iOS APNs、鸿蒙 Push Kit、桌面端 WebSocket 长连接等），并支持 **微信 ClawBot（iLink）**  等补充渠道；你可通过 HTTP API 将消息投递到用户已绑定的端上。 你可以使用 [**WxPusher** ](https://wxpusher.zjiecode.com/) 来做服务器报警通知、抢课通知、抢票通知，信息更新提示等。

**WxPusher 提供覆盖 Android（各厂商）、iOS、鸿蒙、macOS、Windows、Linux 的全平台客户端，手机和电脑都能实时收消息，且客户端全部开源、可自由审计。**  为提升到达率与稳定性，建议用户安装 WxPusher 客户端并按需开启各推送渠道。[查看下载APP](https://wxpusher.zjiecode.com/docs/#/?id=app-download)

## [demo演示程序](https://wxpusher.zjiecode.com/docs/#/?id=demo%e6%bc%94%e7%a4%ba%e7%a8%8b%e5%ba%8f)

你可以访问演示程序，体验功能：[https://wxpusher.zjiecode.com/demo/](https://wxpusher.zjiecode.com/demo/)

演示程序源代码：[https://github.com/wxpusher/wxpusher-sdk-java/](https://github.com/wxpusher/wxpusher-sdk-java/)

管理后台：[https://wxpusher.zjiecode.com/admin/](https://wxpusher.zjiecode.com/admin/)

请一定不要调用demo程序，直接给用户发送消息！！！

## [APP效果预览](https://wxpusher.zjiecode.com/docs/#/?id=app%e6%95%88%e6%9e%9c%e9%a2%84%e8%a7%88)

[点击查看下载APP](https://wxpusher.zjiecode.com/docs/#/?id=app-download)

| 用户登录 | 消息列表 | 消息详情 | 个人中心 |
|---|---|---|---|
| ![](https://aka.doubaocdn.com/s/w5OL1wqMkg) | ![](https://aka.doubaocdn.com/s/MYxC1wqMkg) | ![](https://aka.doubaocdn.com/s/dNup1wqMkg) | ![](https://aka.doubaocdn.com/s/vo9h1wqMkg) |

## [微信ClawBot效果预览](https://wxpusher.zjiecode.com/docs/#/?id=%e5%be%ae%e4%bf%a1clawbot%e6%95%88%e6%9e%9c%e9%a2%84%e8%a7%88)

| 微信内收到推送的预览 | 渠道激活方式 |
|---|---|
| ![](https://aka.doubaocdn.com/s/mMP61wqMkg) | ![](https://aka.doubaocdn.com/s/CDrx1wqMkg) |

# [消息接收通道](https://wxpusher.zjiecode.com/docs/#/?id=%e6%b6%88%e6%81%af%e6%8e%a5%e6%94%b6%e9%80%9a%e9%81%93)

为了追求更好的用户体验，WxPusher 打造了**覆盖手机与电脑的全平台客户端** ：手机端支持 **Android（各厂商）、iOS、鸿蒙** ，电脑端支持 **macOS、Windows、Linux** ，全平台都能实时接收消息，而且客户端全部开源、可自由审计。

## [全平台下载](https://wxpusher.zjiecode.com/docs/#/?id=app-download)

各端形态、推送方式与开源情况一览：

| 平台 | 形态 | 推送方式 | 是否开源 |
|---|---|---|---|
| Android（小米/华为/荣耀/OPPO/VIVO/魅族等） | 手机 App | 各厂商系统推送，后台免保活 | ✅ 开源 |
| iOS | 手机 App | APNs 苹果系统推送 | ✅ 开源 |
| 鸿蒙 HarmonyOS Next | 手机 App | Push Kit 系统级推送，后台免保活 | ✅ 开源 |
| macOS | 桌面客户端 | WebSocket 长连接 + 系统通知 | ✅ 开源 |
| Windows | 桌面客户端 | WebSocket 长连接 + 系统通知 | ✅ 开源 |
| Linux | 桌面客户端 | WebSocket 长连接 + 系统通知 | ✅ 开源 |

**统一下载入口（手机 + 电脑全平台）：[https://wxpusher.zjiecode.com/download/](https://wxpusher.zjiecode.com/download/)**

- 扫码下面二维码下载

![](https://aka.doubaocdn.com/s/7r0P1wqMkg)

## [iOS苹果客户端](https://wxpusher.zjiecode.com/docs/#/?id=ios%e8%8b%b9%e6%9e%9c%e5%ae%a2%e6%88%b7%e7%ab%af)

已经支持iPhone手机，支持APNs后台推送，用户体验更佳，支持iOS 14+，下载方式如下：

- 打开AppStore（苹果应用商店），搜索：WxPusher，下载安装

- [点击这里的链接](https://apps.apple.com/cn/app/wxpusher%E6%B6%88%E6%81%AF%E6%8E%A8%E9%80%81%E5%B9%B3%E5%8F%B0/id6444387603)，直接打开并下载应用

![](https://aka.doubaocdn.com/s/MrI91wqMkg)

## [Android客户端](https://wxpusher.zjiecode.com/docs/#/?id=android%e5%ae%a2%e6%88%b7%e7%ab%af)

### [应用下载](https://wxpusher.zjiecode.com/docs/#/?id=%e5%ba%94%e7%94%a8%e4%b8%8b%e8%bd%bd)

目前Android客户端已经适配国内主要厂商，支持厂商后台推送，无须保持后台运行也可以接收消息。

- 下载链接 [https://wxpusher.zjiecode.com/download/](https://wxpusher.zjiecode.com/download/)

- 扫码下面二维码下载

![](https://aka.doubaocdn.com/s/7r0P1wqMkg)

### [当前厂商适配情况](https://wxpusher.zjiecode.com/docs/#/?id=%e5%bd%93%e5%89%8d%e5%8e%82%e5%95%86%e9%80%82%e9%85%8d%e6%83%85%e5%86%b5)

各大应用市场搜索【WxPusher】或者 【WxPusher消息推送平台】 可以下载

| 品牌\市场 | 后台推送支持情况 | 应用市场上架 |
|---|---|---|
| 小米 | ✅ 完全支持后台接收消息 | ✅是 |
| 华为 | ✅ 完全支持后台接收消息 | ✅是 |
| 苹果 | ✅ 完全支持后台接收消息 | ✅是 |
| 荣耀 | ✅ 完全支持后台接收消息 | ✅是 |
| OPPO | ✅ 完全支持后台接收消息 | ✅是 |
| VIVO | ✅ 完全支持后台接收消息 | ✅是 |
| 魅族 | ✅ 完全支持后台接收消息 | ✅是 |
| 其他安卓手机 | ⚠️ 已实现后台保活接收消息 | - |
| 应用宝 | - | ✅是 |

## [鸿蒙客户端（HarmonyOS Next）](https://wxpusher.zjiecode.com/docs/#/?id=%e9%b8%bf%e8%92%99%e5%ae%a2%e6%88%b7%e7%ab%af%ef%bc%88harmonyos-next%ef%bc%89)

面向 **HarmonyOS Next（纯鸿蒙）**  的原生客户端，使用 ArkTS + ArkUI 开发，与 Android / iOS 功能对齐。

- **系统级推送** ：直接对接鸿蒙 **Push Kit** ，无需后台保活即可接收消息，体验更佳；

- **下载方式** ：在华为应用市场（AppGallery）搜索「WxPusher消息推送平台」，或前往[下载页](https://wxpusher.zjiecode.com/download/)；

- **开源仓库** ：[https://github.com/wxpusher/wxpusher_app_harmoney](https://github.com/wxpusher/wxpusher_app_harmoney)

## [桌面客户端（macOS / Windows / Linux）](https://wxpusher.zjiecode.com/docs/#/?id=%e6%a1%8c%e9%9d%a2%e5%ae%a2%e6%88%b7%e7%ab%af%ef%bc%88macos-windows-linux%ef%bc%89)

面向电脑用户的桌面客户端，基于 Electron + React 构建，**macOS、Windows、Linux 三大系统全覆盖** ，开着电脑就能实时收消息，体验稳定完整。

- **实时推送** ：主进程维护 WebSocket 长连接接收消息，并以系统通知提醒；

- **完整能力** ：扫码登录、消息列表 / 搜索 / 已读 / 批量删除、消息详情、桌面托盘后台驻留、开机自启、自动更新；

- **下载方式** ：前往[下载页](https://wxpusher.zjiecode.com/download/)，提供 苹果电脑（Apple 芯片 / Intel）dmg、Windows exe、Linux deb / rpm 安装包；

- **开源仓库** ：[https://github.com/wxpusher/wxpusher-desktop](https://github.com/wxpusher/wxpusher-desktop)

## [微信 ClawBot（iLink）推送渠道](https://wxpusher.zjiecode.com/docs/#/?id=%e5%be%ae%e4%bf%a1-clawbot%ef%bc%88ilink%ef%bc%89%e6%8e%a8%e9%80%81%e6%b8%a0%e9%81%93)

除 App 内各厂商推送、APNs、WebSocket 长连接等通道外，WxPusher 还支持通过 **微信ClawBot** （微信龙虾渠道）向已绑定用户发送文本通知。

目前仅支持发送消息，暂不支持上行消息。

- **使用方式** ：用户在 **WxPusher App**  内按引导完成微信 ClawBot（iLink）绑定（在我的-推送渠道-绑定微信ClawBot，可以参考[微信 ClawBot（iLink）绑定说明](https://mp.weixin.qq.com/s/lYVNMLRtTNNjKKD7NLZxiA)）。

- **与 API 的关系** ：开发者侧仍使用既有的发送接口；是否走 iLink 由用户是否在 App 中绑定并启用该渠道决定，**不改变 appToken / UID / SPT / 主题等标准推送模型** 。

- **渠道侧限制（重要）** ：用户每在微信侧 **激活**  该渠道后，**24 小时内通过该通道最多接收 10 条推送** ；用尽后需用户向 ClawBot **回复任意内容**  再次激活，方可继续通过该通道接收；渠道即将失效时，用户可能在 App 或微信侧收到激活提醒。

- **说明** ：上述条数与时效来自微信平台 iLink 能力与 WxPusher 投递策略，与下文「单次请求的 UID 数量、全站发送 QPS」等**接口级限制相互独立** 。

| 微信内收到推送的预览 | 渠道激活方式（示意） |
|---|---|
| ![](https://aka.doubaocdn.com/s/mMP61wqMkg) | ![](https://aka.doubaocdn.com/s/CDrx1wqMkg) |

## [客户端开源](https://wxpusher.zjiecode.com/docs/#/?id=%e5%ae%a2%e6%88%b7%e7%ab%af%e5%bc%80%e6%ba%90)

WxPusher 各端客户端均已开源，欢迎查看、审计源码，也欢迎提交 PR 参与共建：

- **Android / iOS 客户端** ：[https://github.com/wxpusher/wxpusher-app](https://github.com/wxpusher/wxpusher-app)

- **鸿蒙客户端（HarmonyOS Next）** ：[https://github.com/wxpusher/wxpusher_app_harmoney](https://github.com/wxpusher/wxpusher_app_harmoney)

- **桌面客户端（macOS / Windows / Linux）** ：[https://github.com/wxpusher/wxpusher-desktop](https://github.com/wxpusher/wxpusher-desktop)

各端均采用「四川思明今创科技有限公司客户端开源协议」，可自由查看和审计全部源代码，具体条款以各仓库的 LICENSE 为准。

# [2种发送方式](https://wxpusher.zjiecode.com/docs/#/?id=_2%e7%a7%8d%e5%8f%91%e9%80%81%e6%96%b9%e5%bc%8f)

为了方便不同的用户群体，不同的使用场景，更快捷方便的发送消息，我们目前支持了2种使用WxPusher的方式。

- **请注意，这2种发送方式，身份标志不一样，不可以相互迁移或者切换;**

- **在有条件的情况下，强烈建议使用第一种方式，能力更佳完善。**

| 发送方式 | 优点、缺点和适用场景 |
|---|---|
| 标准推送【推荐】
(标准应用开发) | - 发送消息和接收消息的不是同一个人
- 可以管理接收消息的用户
- 可以支持上行消息等高级功能
- 适合有一定开发经验的开发者
- 无特殊限制，具体可以查看[限制说明](https://wxpusher.zjiecode.com/docs/#/?id=limit) |
| 极简推送
（SPT一键推送） | - 发送消息和接收消息的是同一个人
- 非常简单，无需登陆，创建应用等
- 简单发送消息能力，无法管理消息和接收者
- 适合无经验但是想简单发送消息的用户
- 最多一次发送给10个人，具体说明请查看[极简推送接口](https://wxpusher.zjiecode.com/docs/#/?id=spt) |

# [方式一：标准推送](https://wxpusher.zjiecode.com/docs/#/?id=standard)

## [名词解释](https://wxpusher.zjiecode.com/docs/#/?id=%e5%90%8d%e8%af%8d%e8%a7%a3%e9%87%8a)

- 应用

对应你的一个项目 ，主要用来做鉴权，资源隔离等（类比使用高德地图SDK、微信登录等，都会先新建一个应用），每个应用拥有独立的名字，二维码，回调地址，调用资源，鉴权信息等，发送消息第一步，需要先新建一个应用。

简单的理解，你有一个抢火车票的项目，抢到票了需要给用户发送信息；你还有一个服务器报警的项目，服务器有异常的时候，给相关负责人发送信息，这2个的用途是不一样的，你就可以创建2个应用来分别发送他们的信息。

用户可以通过二维码或者链接关注这个应用，关注我们会把用户的UID回调给你指定的服务器，你可以通过UID给这个用户发送信息。

- 主题(Topic)

主题(Topic)是应用下面，一类消息的集合，比如创建了一个优惠相关的应用，用来给用户推送各种优惠信息，但是不同的用户关注的优惠信息不同，一部分人关注淘宝的，一部分人关注京东的。这种场景下，你就可以创建一个淘宝的主题，再创建一个京东的主题，发送信息的时候，直接发送到对应的主题即可，每个主题都有对应的订阅链接和二维码，用户订阅这个主题以后，就能接收这个主题下的信息了。

Topic只能无差别群发，不能针对用户定制消息，用户关注以后，无回调信息 。

- 应用和主题(Topic)的对比

| 项目 | 应用 | 主题(Topic) |
|---|---|---|
| 概念 | 应用是一个独立的个体 | 主题属于应用，调用主题需要使用对应应用的APP_TOKEN授权 |
| 关注方式 | 二维码和链接 | 二维码和链接 |
| 发送群体 | 通过UID一对一发送 | 消息发送主题后，主题再分发给关注主题的用户，属于群发 |

- 各种二维码

| 项目 | 应用二维码 | 主题二维码 |
|---|---|---|
| 用途 | 用于微信用户关注应用，用户只有关注了你的应用，
你才能拿到他的UID，才能给他发送信息 | 用于订阅主题，用户订阅主题以后，你不能拿到它的UID |
| 动静态 | 默认动态二维码 | 默认动态二维码 |

**动态二维码** ：二维码链接不会变，但是二维码图形会变 ，因此只能使用动态二维码链接，不对截图、打印等。

**静态二维码** ：二维码链接和图形都不变，可以随意使用。

- APP_TOKEN

应用的身份标志，这个只能开发者你本人知道 ，拥有APP_TOKEN，就可以给对应的应用的用户发送消息 ，所以请严格保密，不要发送到github之类的地方。

- UID

微信用户标志，在单独给某个用户发送消息时，来说明要发给哪个用户。

## [快速接入](https://wxpusher.zjiecode.com/docs/#/?id=%e5%bf%ab%e9%80%9f%e6%8e%a5%e5%85%a5)

### [整体架构](https://wxpusher.zjiecode.com/docs/#/?id=%e6%95%b4%e4%bd%93%e6%9e%b6%e6%9e%84)

在接入之前，你可以看一下架构图，有助于你理解单发，群发的区别。 ![](https://aka.doubaocdn.com/s/bPmp1wqMkg)

### [注册并且创建应用](https://wxpusher.zjiecode.com/docs/#/?id=%e6%b3%a8%e5%86%8c%e5%b9%b6%e4%b8%94%e5%88%9b%e5%bb%ba%e5%ba%94%e7%94%a8)

[https://wxpusher.zjiecode.com/admin/](https://wxpusher.zjiecode.com/admin/) ，使用微信扫码登录，无需注册，新用户首次扫码自动注册。

创建一个应用，如下图：

![](https://aka.doubaocdn.com/s/dYwH1wqMkg)

回调地址：可以不填写，不填写用户关注的时候，就不会有回调，你不能拿到用户的UID，参考[回调说明](https://wxpusher.zjiecode.com/docs/#/?id=callback)。

设置URL：可以不填写，填写以后，用户在微信端打开「我的订阅」，可以直接跳转到这个地址，并且会携带uid作为参数，方便做定制化页面展示。

联系方式：可以不填写，告诉用户，如何联系到你，给你反馈问题。

关注提示：用户关注或者扫应用码的时候发送给用户的提示，你可以不填写，Wxpusher会提供一个默认文案。你也可以在用户关注回调给你UID的时候，再主动推送一个提示消息给用户。

说明：描述一下，你的应用，推送的是啥内容，用户通过链接关注，或者在微信端查看的时候可以看到。

### [获取appToken](https://wxpusher.zjiecode.com/docs/#/?id=%e8%8e%b7%e5%8f%96apptoken)

在你创建应用的过程中，你应该已经看到appToken，如果没有保存，可以通过下面的方式重置它。

打开应用的后台[https://wxpusher.zjiecode.com/admin/](https://wxpusher.zjiecode.com/admin/)，从左侧菜单栏，找到appToken菜单，在这里，你可以重置appToken，请注意，重置后，老的appToken会立即失效，调用接口会失败。

![](https://aka.doubaocdn.com/s/NgaK1wqMkg)

### [扫码关注应用](https://wxpusher.zjiecode.com/docs/#/?id=%e6%89%ab%e7%a0%81%e5%85%b3%e6%b3%a8%e5%ba%94%e7%94%a8)

创建应用以后，你可以看到应用的应用码和关注链接，你可以让你的用户通过下面2种方式来关注你的应用，关注你的应用以后，你就可以给他发送消息了。

![](https://aka.doubaocdn.com/s/9J0T1wqMkg)

### [获取UID](https://wxpusher.zjiecode.com/docs/#/?id=%e8%8e%b7%e5%8f%96uid)

目前有3种方式获取UID：

1. 关注公众号：wxpusher，然后点击「我的」-「我的UID」查询到UID；

2. 通过[创建参数二维码](https://wxpusher.zjiecode.com/docs/#/?id=create-qrcode)接口创建一个定制的二维码，用户扫描此二维码后，会通过[用户关注回调](https://wxpusher.zjiecode.com/docs/#/?id=subscribe-callback)把UID推送给你；

3. 通过[创建参数二维码](https://wxpusher.zjiecode.com/docs/#/?id=create-qrcode)接口创建一个定制的二维码，然后用[查询扫码用户UID](https://wxpusher.zjiecode.com/docs/#/?id=query-uid)接口，查询扫描此二维码的用户UID；

### [发送消息](https://wxpusher.zjiecode.com/docs/#/?id=%e5%8f%91%e9%80%81%e6%b6%88%e6%81%af)

拿到UID以后，配合应用的appToken，然后调用发送接口发送消息。

## [HTTP接口说明](https://wxpusher.zjiecode.com/docs/#/?id=http%e6%8e%a5%e5%8f%a3%e8%af%b4%e6%98%8e)

所有接口均已经支持https。

### [发送消息](https://wxpusher.zjiecode.com/docs/#/?id=send-msg)

- POST接口 POST接口是功能完整的接口，推荐使用。

Content-Type:application/json

地址：[https://wxpusher.zjiecode.com/api/send/message](https://wxpusher.zjiecode.com/api/send/message)

请求数据放在body里面，具体参数如下：

**JSON不支持注释，发送的时候，需要删除注释。**
```
{
 "appToken":"AT_xxx",//必传
 "content":"<h1>H1标题</h1>
<p style=\"color:red;\">欢迎你使用WxPusher，推荐使用HTML发送</p>",//必传
 //消息摘要；接口侧最长100，可以不传，不传默认截取 content 前面内容。各端通知/卡片实际展示可能更短（如部分场景约20字）。
 "summary":"消息摘要",
 //内容类型 1表示文字 2表示html(只发送body标签内部的数据即可，不包括body标签，推荐使用这种) 3表示markdown 
 "contentType":2,
 //发送目标的topicId，是一个数组！！！，也就是群发，使用uids单发的时候， 可以不传。
 "topicIds":[ 
 123
 ],
 //发送目标的UID，是一个数组。注意uids和topicIds可以同时填写，也可以只填写一个。
 "uids":[
 "UID_xxxx"
 ],
 //原文链接，可选参数
 "url":"https://wxpusher.zjiecode.com", 
 //是否验证订阅时间，true表示只推送给付费订阅用户，false表示推送的时候，不验证付费，不验证用户订阅到期时间，用户订阅过期了，也能收到。
 //verifyPay字段即将被废弃，请使用verifyPayType字段，传verifyPayType会忽略verifyPay
 "verifyPay":false, 
 //是否验证订阅时间，0：不验证，1:只发送给付费的用户，2:只发送给未订阅或者订阅过期的用户
 "verifyPayType":0 
}
```

html格式的消息（contentType=2），支持通过标签复制，复制的语法如下：
```
