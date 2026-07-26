from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import smtplib
import time
import urllib.parse
from abc import ABC, abstractmethod
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any

import requests


FieldSchema = dict[str, Any]


def field(label: str, *, required: bool = False, secret: bool = False, kind: str = "text", default: Any = None) -> FieldSchema:
    return {"label": label, "required": required, "secret": secret, "type": kind, "default": default}


def compact(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in (None, "")}


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(";") if item.strip()]


def parse_bool(value: Any, default: bool = False) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_int(value: Any, default: int = 0) -> int:
    if value in (None, ""):
        return default
    return int(value)


def parse_json_value(value: Any, default: Any = None) -> Any:
    if value in (None, ""):
        return default
    if isinstance(value, str):
        return json.loads(value)
    return value


def require(config: dict[str, Any], *keys: str) -> None:
    missing = [key for key in keys if config.get(key) in (None, "")]
    if missing:
        raise ValueError(f"缺少必填配置: {', '.join(missing)}")


def json_or_text(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def ok_detail(name: str) -> tuple[bool, str]:
    return True, f"{name} 推送成功"


def response_error(name: str, data: Any) -> tuple[bool, str]:
    return False, f"{name} 返回异常: {data}"


class ChannelSender(ABC):
    type_name: str
    label: str
    target_mode = "embedded"
    target_label: str | None = None
    config_schema: dict[str, FieldSchema] = {}

    def validate_config(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        config = dict(raw_config)
        for key, schema in self.config_schema.items():
            if key not in config and schema.get("default") not in (None, ""):
                config[key] = schema["default"]
            if schema.get("type") == "number" and config.get(key) not in (None, ""):
                config[key] = parse_int(config[key])
            if schema.get("type") == "boolean" and config.get(key) not in (None, ""):
                config[key] = parse_bool(config[key])
        require(config, *[key for key, schema in self.config_schema.items() if schema.get("required")])
        return compact(config)

    @abstractmethod
    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        raise NotImplementedError


class ConsoleSender(ChannelSender):
    type_name = "console"
    label = "控制台"
    config_schema = {}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        return True, f"{title}\n\n{content}"


class BarkSender(ChannelSender):
    type_name = "bark"
    label = "Bark"
    config_schema = {
        "bark_base_url": field("Bark URL、设备码或 API 地址", required=True),
        "bark_device_key": field("设备 key；群发多个用英文逗号分隔"),
        "bark_device_keys": field("批量设备 key；多个用英文逗号分隔"),
        "bark_subtitle": field("副标题"),
        "bark_markdown": field("Markdown 正文；支持 # 一级标题、## 二级标题"),
        "bark_group": field("分组"),
        "bark_sound": field("声音"),
        "bark_icon": field("图标 URL"),
        "bark_level": field("时效等级"),
        "bark_url": field("点击跳转 URL"),
        "bark_archive": field("是否存档"),
        "bark_badge": field("角标数字", kind="number"),
        "bark_volume": field("重要提醒音量 0-10", kind="number"),
        "bark_auto_copy": field("自动复制", kind="boolean"),
        "bark_copy": field("复制内容"),
        "bark_call": field("重复提醒", kind="boolean"),
        "bark_ciphertext": field("密文"),
        "bark_image": field("图片 URL"),
        "bark_action": field("操作参数"),
        "bark_id": field("消息 ID"),
        "bark_delete": field("删除消息 ID"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        url = config["bark_base_url"]
        if url.startswith("http") and config.get("bark_device_key") and not url.rstrip("/").endswith("/push"):
            parsed = urllib.parse.urlparse(url)
            url = f"{parsed.scheme}://{parsed.netloc}/push"
        elif not url.startswith("http"):
            url = f"https://api.day.app/{url}"
        payload = {"title": title}
        if config.get("bark_markdown"):
            payload["markdown"] = config["bark_markdown"]
        elif config.get("_notify_content_type") == "markdown":
            payload["markdown"] = content
        else:
            payload["body"] = content
        if config.get("bark_device_keys"):
            payload["device_keys"] = [
                item.strip() for item in str(config["bark_device_keys"]).split(",") if item.strip()
            ]
        for source, dest in {
            "bark_device_key": "device_key",
            "bark_subtitle": "subtitle",
            "bark_group": "group",
            "bark_sound": "sound",
            "bark_icon": "icon",
            "bark_level": "level",
            "bark_url": "url",
            "bark_archive": "isArchive",
            "bark_badge": "badge",
            "bark_volume": "volume",
            "bark_auto_copy": "autoCopy",
            "bark_copy": "copy",
            "bark_call": "call",
            "bark_ciphertext": "ciphertext",
            "bark_image": "image",
            "bark_action": "action",
            "bark_id": "id",
            "bark_delete": "delete",
        }.items():
            if config.get(source) not in (None, ""):
                payload[dest] = config[source]
        data = requests.post(url, json=payload, timeout=15).json()
        return ok_detail(self.label) if data.get("code") == 200 else response_error(self.label, data)


class DingtalkSender(ChannelSender):
    type_name = "dingtalk_bot"
    label = "钉钉机器人"
    config_schema = {
        "dd_bot_token": field("机器人 access_token", required=True, secret=True),
        "dd_bot_secret": field("签名密钥", secret=True),
        "dd_msgtype": field("消息类型 text/markdown/link/actionCard/feedCard", default="text"),
        "dd_markdown_text": field("Markdown 内容"),
        "dd_link_url": field("Link 消息 URL"),
        "dd_pic_url": field("图片 URL"),
        "dd_btn_orientation": field("ActionCard 按钮排列 0/1"),
        "dd_btns": field("ActionCard 按钮 JSON 数组"),
        "dd_feed_links": field("FeedCard links JSON 数组"),
        "dd_payload": field("原始钉钉 payload JSON；填写后优先使用"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        extra = ""
        if config.get("dd_bot_secret"):
            timestamp = str(round(time.time() * 1000))
            sign = hmac.new(
                config["dd_bot_secret"].encode(),
                f"{timestamp}\n{config['dd_bot_secret']}".encode(),
                digestmod=hashlib.sha256,
            ).digest()
            extra = f"&timestamp={timestamp}&sign={urllib.parse.quote_plus(base64.b64encode(sign))}"
        url = f"https://oapi.dingtalk.com/robot/send?access_token={config['dd_bot_token']}{extra}"
        payload = parse_json_value(config.get("dd_payload"))
        if not payload:
            msgtype = config.get("dd_msgtype") or "text"
            if msgtype == "markdown":
                payload = {"msgtype": "markdown", "markdown": {"title": title, "text": config.get("dd_markdown_text") or f"## {title}\n\n{content}"}}
            elif msgtype == "link":
                payload = {"msgtype": "link", "link": {"title": title, "text": content, "messageUrl": config.get("dd_link_url", ""), "picUrl": config.get("dd_pic_url", "")}}
            elif msgtype == "actionCard":
                payload = {"msgtype": "actionCard", "actionCard": {"title": title, "text": config.get("dd_markdown_text") or content, "btnOrientation": config.get("dd_btn_orientation", "0"), "btns": parse_json_value(config.get("dd_btns"), [])}}
            elif msgtype == "feedCard":
                payload = {"msgtype": "feedCard", "feedCard": {"links": parse_json_value(config.get("dd_feed_links"), [])}}
            else:
                payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
        data = requests.post(url, json=payload, timeout=15).json()
        return ok_detail(self.label) if data.get("errcode") == 0 else response_error(self.label, data)


class FeishuSender(ChannelSender):
    type_name = "feishu_bot"
    label = "飞书/Lark 机器人"
    config_schema = {
        "fskey": field("Webhook key 或完整 URL", required=True, secret=True),
        "fssecret": field("签名密钥", secret=True),
        "fs_msg_type": field("消息类型 text/post/interactive", default="text"),
        "fs_post": field("富文本 post JSON"),
        "fs_card": field("交互卡片 JSON"),
        "fs_payload": field("原始飞书 payload JSON；填写后优先使用"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        url = config["fskey"] if config["fskey"].startswith("http") else f"https://open.feishu.cn/open-apis/bot/v2/hook/{config['fskey']}"
        payload = parse_json_value(config.get("fs_payload"))
        if not payload:
            msg_type = config.get("fs_msg_type") or "text"
            if msg_type == "post":
                payload = {"msg_type": "post", "content": {"post": parse_json_value(config.get("fs_post"), {"zh_cn": {"title": title, "content": [[{"tag": "text", "text": content}]]}})}}
            elif msg_type == "interactive":
                payload = {"msg_type": "interactive", "card": parse_json_value(config.get("fs_card"), {})}
            else:
                payload = {"msg_type": "text", "content": {"text": f"{title}\n\n{content}"}}
        if config.get("fssecret"):
            timestamp = str(int(time.time()))
            sign = hmac.new(f"{timestamp}\n{config['fssecret']}".encode(), digestmod=hashlib.sha256).digest()
            payload.update({"timestamp": timestamp, "sign": base64.b64encode(sign).decode()})
        data = requests.post(url, json=payload, timeout=15).json()
        return ok_detail(self.label) if data.get("StatusCode") == 0 or data.get("code") == 0 else response_error(self.label, data)


class GoCqHttpSender(ChannelSender):
    type_name = "go_cqhttp"
    label = "go-cqhttp"
    config_schema = {
        "gobot_url": field("接口 URL", required=True),
        "gobot_qq": field("目标参数，如 user_id=10000 或 group_id=10000", required=True),
        "gobot_token": field("access_token", secret=True),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        params = {"message": f"标题:{title}\n内容:{content}"}
        if config.get("gobot_token"):
            params["access_token"] = config["gobot_token"]
        url = f"{config['gobot_url']}?{config['gobot_qq']}"
        data = requests.get(url, params=params, timeout=15).json()
        return ok_detail(self.label) if data.get("status") == "ok" or data.get("retcode") == 0 else response_error(self.label, data)


class GotifySender(ChannelSender):
    type_name = "gotify"
    label = "Gotify"
    config_schema = {
        "gotify_url": field("Gotify 地址", required=True),
        "gotify_token": field("应用 token", required=True, secret=True),
        "gotify_priority": field("优先级", kind="number", default=0),
        "gotify_extras": field("extras JSON"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        payload = {"title": title, "message": content, "priority": config.get("gotify_priority", 0)}
        extras = parse_json_value(config.get("gotify_extras"))
        if extras:
            payload["extras"] = extras
        data = requests.post(f"{config['gotify_url'].rstrip('/')}/message", params={"token": config["gotify_token"]}, json=payload, timeout=15).json()
        return ok_detail(self.label) if data.get("id") else response_error(self.label, data)


class IGotSender(ChannelSender):
    type_name = "igot"
    label = "iGot"
    config_schema = {"igot_push_key": field("iGot push key", required=True, secret=True)}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        data = requests.post(f"https://push.hellyw.com/{config['igot_push_key']}", data={"title": title, "content": content}, timeout=15).json()
        return ok_detail(self.label) if data.get("ret") == 0 else response_error(self.label, data)


class ServerChanSender(ChannelSender):
    type_name = "server_chan"
    label = "Server 酱"
    config_schema = {"push_key": field("SendKey", required=True, secret=True)}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        match = re.match(r"sctp(\d+)t", config["push_key"])
        url = f"https://{match.group(1)}.push.ft07.com/send/{config['push_key']}.send" if match else f"https://sctapi.ftqq.com/{config['push_key']}.send"
        data = requests.post(url, data={"text": title, "desp": content.replace("\n", "\n\n")}, timeout=15).json()
        return ok_detail(self.label) if data.get("errno") == 0 or data.get("code") == 0 else response_error(self.label, data)


class PushDeerSender(ChannelSender):
    type_name = "pushdeer"
    label = "PushDeer"
    config_schema = {
        "deer_key": field("PushDeer key", required=True, secret=True),
        "deer_url": field("自定义 API URL"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        url = config.get("deer_url") or "https://api2.pushdeer.com/message/push"
        data = requests.post(url, data={"text": title, "desp": content, "type": "markdown", "pushkey": config["deer_key"]}, timeout=15).json()
        return ok_detail(self.label) if data.get("content", {}).get("result") else response_error(self.label, data)


class SynologyChatSender(ChannelSender):
    type_name = "synology_chat"
    label = "Synology Chat"
    config_schema = {"chat_url": field("Chat webhook URL", required=True), "chat_token": field("Token，可留空如果 URL 已包含", secret=True)}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        url = config["chat_url"] + config.get("chat_token", "")
        response = requests.post(url, data="payload=" + json.dumps({"text": title + "\n" + content}), timeout=15)
        data = json_or_text(response)
        return ok_detail(self.label) if response.status_code == 200 else response_error(self.label, data)


class PushPlusSender(ChannelSender):
    type_name = "pushplus"
    label = "PushPlus"
    config_schema = {
        "push_plus_token": field("用户令牌", required=True, secret=True),
        "push_plus_user": field("群组编码"),
        "push_plus_template": field("模板", default="html"),
        "push_plus_channel": field("渠道", default="wechat"),
        "push_plus_webhook": field("Webhook 编码"),
        "push_plus_callback_url": field("回调 URL"),
        "push_plus_to": field("好友令牌/企业微信用户 ID"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        data = requests.post("https://www.pushplus.plus/send", json={
            "token": config["push_plus_token"], "title": title, "content": content,
            "topic": config.get("push_plus_user", ""), "template": config.get("push_plus_template", "html"),
            "channel": config.get("push_plus_channel", "wechat"), "webhook": config.get("push_plus_webhook", ""),
            "callbackUrl": config.get("push_plus_callback_url", ""), "to": config.get("push_plus_to", ""),
        }, timeout=15).json()
        return ok_detail(self.label) if data.get("code") == 200 else response_error(self.label, data)


class WePlusSender(ChannelSender):
    type_name = "weplus_bot"
    label = "微加机器人"
    config_schema = {
        "we_plus_bot_token": field("用户令牌", required=True, secret=True),
        "we_plus_bot_receiver": field("接收者"),
        "we_plus_bot_version": field("版本", default="pro"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        template = "html" if len(content) > 800 else "txt"
        data = requests.post("https://www.weplusbot.com/send", json={"token": config["we_plus_bot_token"], "title": title, "content": content, "template": template, "receiver": config.get("we_plus_bot_receiver", ""), "version": config.get("we_plus_bot_version", "pro")}, timeout=15).json()
        return ok_detail(self.label) if data.get("code") == 200 else response_error(self.label, data)


class QmsgSender(ChannelSender):
    type_name = "qmsg"
    label = "Qmsg 酱"
    config_schema = {"qmsg_key": field("QMSG_KEY", required=True, secret=True), "qmsg_type": field("QMSG_TYPE", required=True)}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        data = requests.post(f"https://qmsg.zendee.cn/{config['qmsg_type']}/{config['qmsg_key']}", params={"msg": f"{title}\n\n{content.replace('----', '-')}"}, timeout=15).json()
        return ok_detail(self.label) if data.get("code") == 0 else response_error(self.label, data)


class WeComBotSender(ChannelSender):
    type_name = "wecom_bot"
    label = "企业微信机器人"
    config_schema = {
        "qywx_key": field("机器人 key", required=True, secret=True),
        "qywx_origin": field("企业微信 API Origin", default="https://qyapi.weixin.qq.com"),
        "qywx_msgtype": field("消息类型 text/markdown/image/news/file/template_card", default="text"),
        "qywx_markdown": field("Markdown 内容"),
        "qywx_payload": field("原始企业微信机器人 payload JSON；填写后优先使用"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        origin = config.get("qywx_origin") or "https://qyapi.weixin.qq.com"
        payload = parse_json_value(config.get("qywx_payload"))
        if not payload:
            msgtype = config.get("qywx_msgtype") or "text"
            if msgtype == "markdown":
                payload = {"msgtype": "markdown", "markdown": {"content": config.get("qywx_markdown") or f"## {title}\n\n{content}"}}
            else:
                payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
        data = requests.post(f"{origin}/cgi-bin/webhook/send?key={config['qywx_key']}", json=payload, timeout=15).json()
        return ok_detail(self.label) if data.get("errcode") == 0 else response_error(self.label, data)


class WeComAppSender(ChannelSender):
    type_name = "wecom_app"
    label = "企业微信应用"
    config_schema = {"qywx_am": field("corpid,corpsecret,touser,agentid[,media_id]", required=True, secret=True), "qywx_origin": field("企业微信 API Origin", default="https://qyapi.weixin.qq.com")}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        parts = [item.strip() for item in config["qywx_am"].split(",")]
        if len(parts) not in (4, 5):
            raise ValueError("qywx_am 格式必须为 corpid,corpsecret,touser,agentid[,media_id]")
        corpid, corpsecret, touser, agentid = parts[:4]
        media_id = parts[4] if len(parts) == 5 else ""
        origin = config.get("qywx_origin") or "https://qyapi.weixin.qq.com"
        token = requests.post(f"{origin}/cgi-bin/gettoken", params={"corpid": corpid, "corpsecret": corpsecret}, timeout=15).json()["access_token"]
        payload: dict[str, Any] = {"touser": touser, "agentid": agentid, "safe": "0"}
        if media_id:
            payload.update({"msgtype": "mpnews", "mpnews": {"articles": [{"title": title, "thumb_media_id": media_id, "author": "push-aio", "content_source_url": "", "content": content.replace("\n", "<br/>"), "digest": content}]}})
        else:
            payload.update({"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}})
        data = requests.post(f"{origin}/cgi-bin/message/send?access_token={token}", json=payload, timeout=15).json()
        return ok_detail(self.label) if data.get("errcode") == 0 or data.get("errmsg") == "ok" else response_error(self.label, data)


class TelegramSender(ChannelSender):
    type_name = "telegram_bot"
    label = "Telegram Bot"
    config_schema = {
        "tg_bot_token": field("Bot token", required=True, secret=True),
        "tg_user_id": field("Chat ID", required=True),
        "tg_api_host": field("API Host"),
        "tg_proxy_auth": field("代理认证"),
        "tg_proxy_host": field("代理 Host"),
        "tg_proxy_port": field("代理 Port"),
        "tg_parse_mode": field("解析模式 MarkdownV2/HTML/Markdown"),
        "tg_disable_web_page_preview": field("禁用链接预览", kind="boolean", default=True),
        "tg_disable_notification": field("静默发送", kind="boolean"),
        "tg_protect_content": field("保护内容", kind="boolean"),
        "tg_message_thread_id": field("话题 ID", kind="number"),
        "tg_reply_markup": field("reply_markup JSON"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        api_host = config.get("tg_api_host") or "https://api.telegram.org"
        proxies = None
        if config.get("tg_proxy_host") and config.get("tg_proxy_port"):
            auth = f"{config['tg_proxy_auth']}@" if config.get("tg_proxy_auth") else ""
            proxy = f"http://{auth}{config['tg_proxy_host']}:{config['tg_proxy_port']}"
            proxies = {"http": proxy, "https": proxy}
        payload: dict[str, Any] = {
            "chat_id": str(config["tg_user_id"]),
            "text": f"{title}\n\n{content}",
            "disable_web_page_preview": parse_bool(config.get("tg_disable_web_page_preview"), True),
        }
        for key, target_key in {
            "tg_parse_mode": "parse_mode",
            "tg_disable_notification": "disable_notification",
            "tg_protect_content": "protect_content",
            "tg_message_thread_id": "message_thread_id",
        }.items():
            if config.get(key) not in (None, ""):
                payload[target_key] = config[key]
        if config.get("tg_reply_markup"):
            payload["reply_markup"] = parse_json_value(config["tg_reply_markup"])
        data = requests.post(f"{api_host}/bot{config['tg_bot_token']}/sendMessage", json=payload, proxies=proxies, timeout=15).json()
        return ok_detail(self.label) if data.get("ok") else response_error(self.label, data)


class AibotkSender(ChannelSender):
    type_name = "aibotk"
    label = "智能微秘书"
    config_schema = {"aibotk_key": field("API key", required=True, secret=True), "aibotk_type": field("room 或 contact", required=True), "aibotk_name": field("群名或好友昵称", required=True)}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        is_room = config["aibotk_type"] == "room"
        url = "https://api-bot.aibotk.com/openapi/v1/chat/room" if is_room else "https://api-bot.aibotk.com/openapi/v1/chat/contact"
        data = {"apiKey": config["aibotk_key"], "message": {"type": 1, "content": f"【青龙快讯】\n\n{title}\n{content}"}}
        data["roomName" if is_room else "name"] = config["aibotk_name"]
        res = requests.post(url, json=data, timeout=15).json()
        return ok_detail(self.label) if res.get("code") == 0 else response_error(self.label, res)


class EmailSender(ChannelSender):
    type_name = "email"
    label = "SMTP 邮件"
    target_mode = "external"
    target_label = "收件邮箱，多个用英文分号分隔；不填则发给自己"
    config_schema = {
        "smtp_host": field("SMTP 主机；也兼容 imap_host 自动转换", required=True),
        "smtp_port": field("SMTP 端口", kind="number", default=465),
        "use_ssl": field("是否启用 SSL", kind="boolean", default=True),
        "email": field("发件邮箱", required=True),
        "auth_code": field("SMTP 授权码", required=True, secret=True),
        "from_name": field("发件人名称", default="push-aio"),
    }

    def validate_config(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        config = dict(raw_config)
        if not config.get("smtp_host") and config.get("imap_host"):
            config["smtp_host"] = str(config["imap_host"]).replace("imap.", "smtp.", 1)
        return super().validate_config(config)

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        to_addrs = split_semicolon(target) or [config["email"]]
        content_type = "html" if config.get("_content_type") == "html" else "plain"
        attachments = config.get("_attachments") or []
        if attachments:
            message = MIMEMultipart("mixed")
            message.attach(MIMEText(content, content_type, "utf-8"))
            for item in attachments:
                filename = item.get("filename")
                raw_content = item.get("content_base64")
                if not filename or not raw_content:
                    raise ValueError("邮件附件必须包含 filename 和 content_base64")
                if "," in raw_content and raw_content.strip().startswith("data:"):
                    raw_content = raw_content.split(",", 1)[1]
                maintype, _, subtype = (item.get("content_type") or "application/octet-stream").partition("/")
                part = MIMEBase(maintype or "application", subtype or "octet-stream")
                part.set_payload(base64.b64decode(raw_content))
                encoders.encode_base64(part)
                if item.get("inline_content_id"):
                    part.add_header("Content-Disposition", "inline", filename=filename)
                    part.add_header("Content-ID", f"<{item['inline_content_id']}>")
                else:
                    part.add_header("Content-Disposition", "attachment", filename=filename)
                message.attach(part)
        else:
            message = MIMEText(content, content_type, "utf-8")
        message["Subject"] = Header(title, "utf-8")
        message["From"] = formataddr((str(Header(config.get("from_name", "push-aio"), "utf-8")), config["email"]))
        message["To"] = ";".join(to_addrs)
        client = smtplib.SMTP_SSL(config["smtp_host"], config.get("smtp_port", 465), timeout=15) if parse_bool(config.get("use_ssl"), True) else smtplib.SMTP(config["smtp_host"], config.get("smtp_port", 25), timeout=15)
        try:
            if not parse_bool(config.get("use_ssl"), True):
                client.starttls()
            client.login(config["email"], config["auth_code"])
            client.sendmail(config["email"], to_addrs, message.as_string())
        finally:
            client.quit()
        return ok_detail(self.label)


class PushMeSender(ChannelSender):
    type_name = "pushme"
    label = "PushMe"
    config_schema = {"pushme_key": field("PushMe key", required=True, secret=True), "pushme_url": field("PushMe URL", default="https://push.i-i.me/")}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        response = requests.post(config.get("pushme_url") or "https://push.i-i.me/", data={"push_key": config["pushme_key"], "title": title, "content": content}, timeout=15)
        return ok_detail(self.label) if response.status_code == 200 and response.text == "success" else response_error(self.label, f"{response.status_code} {response.text}")


class ChronocatSender(ChannelSender):
    type_name = "chronocat"
    label = "Chronocat"
    config_schema = {"chronocat_url": field("Chronocat URL", required=True), "chronocat_qq": field("user_id=... 或 group_id=...", required=True), "chronocat_token": field("Token", required=True, secret=True)}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        user_ids = re.findall(r"user_id=(\d+)", config["chronocat_qq"])
        group_ids = re.findall(r"group_id=(\d+)", config["chronocat_qq"])
        url = f"{config['chronocat_url'].rstrip('/')}/api/message/send"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {config['chronocat_token']}"}
        sent = 0
        for chat_type, ids in [(1, user_ids), (2, group_ids)]:
            for chat_id in ids:
                payload = {"peer": {"chatType": chat_type, "peerUin": chat_id}, "elements": [{"elementType": 1, "textElement": {"content": f"{title}\n\n{content}"}}]}
                response = requests.post(url, headers=headers, json=payload, timeout=15)
                if response.status_code != 200:
                    return response_error(self.label, response.text)
                sent += 1
        return (ok_detail(self.label) if sent else (False, "Chronocat 未匹配到 user_id 或 group_id"))


def parse_headers(headers: str | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not headers:
        return parsed
    for line in headers.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()
    return parsed


def replace_vars(value: str, title: str, content: str) -> str:
    return value.replace("$title", title).replace("$content", content)


class WebhookSender(ChannelSender):
    type_name = "webhook"
    label = "自定义 Webhook"
    config_schema = {
        "webhook_url": field("请求 URL，支持 $title/$content", required=True),
        "webhook_method": field("请求方法", required=True, default="POST"),
        "webhook_content_type": field("Content-Type", default="application/json"),
        "webhook_headers": field("请求头，每行 key: value"),
        "webhook_body": field("请求体，支持 $title/$content"),
    }

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        if "$title" not in config["webhook_url"] and "$title" not in config.get("webhook_body", ""):
            raise ValueError("URL 或 Body 中必须包含 $title")
        headers = parse_headers(config.get("webhook_headers"))
        if config.get("webhook_content_type"):
            headers.setdefault("Content-Type", config["webhook_content_type"])
        url = config["webhook_url"].replace("$title", urllib.parse.quote_plus(title)).replace("$content", urllib.parse.quote_plus(content))
        body = replace_vars(config.get("webhook_body", ""), title, content) if config.get("webhook_body") else None
        response = requests.request(config["webhook_method"].upper(), url, headers=headers, data=body, timeout=15)
        return ok_detail(self.label) if 200 <= response.status_code < 300 else response_error(self.label, f"{response.status_code} {response.text}")


class NtfySender(ChannelSender):
    type_name = "ntfy"
    label = "ntfy"
    config_schema = {
        "ntfy_url": field("ntfy 地址", default="https://ntfy.sh"),
        "ntfy_topic": field("Topic", required=True),
        "ntfy_priority": field("优先级", default="3"),
        "ntfy_token": field("Bearer token", secret=True),
        "ntfy_username": field("用户名"),
        "ntfy_password": field("密码", secret=True),
        "ntfy_actions": field("Actions"),
        "ntfy_tags": field("标签，多个用英文逗号分隔"),
        "ntfy_click": field("点击 URL"),
        "ntfy_attach": field("附件 URL"),
        "ntfy_filename": field("附件文件名"),
        "ntfy_delay": field("延迟发送"),
        "ntfy_markdown": field("启用 Markdown", kind="boolean"),
        "ntfy_email": field("同时转发到邮箱"),
    }

    @staticmethod
    def encode_rfc2047(text: str) -> str:
        return f"=?utf-8?B?{base64.b64encode(text.encode()).decode()}?="

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        headers = {"Title": self.encode_rfc2047(title), "Priority": str(config.get("ntfy_priority", "3")), "Icon": "https://qn.whyour.cn/logo.png"}
        for key, header in {
            "ntfy_tags": "Tags",
            "ntfy_click": "Click",
            "ntfy_attach": "Attach",
            "ntfy_filename": "Filename",
            "ntfy_delay": "Delay",
            "ntfy_email": "Email",
        }.items():
            if config.get(key):
                headers[header] = str(config[key])
        if parse_bool(config.get("ntfy_markdown")) or config.get("_notify_content_type") == "markdown":
            headers["Markdown"] = "yes"
        if config.get("ntfy_token"):
            headers["Authorization"] = "Bearer " + config["ntfy_token"]
        elif config.get("ntfy_username") and config.get("ntfy_password"):
            headers["Authorization"] = "Basic " + base64.b64encode(f"{config['ntfy_username']}:{config['ntfy_password']}".encode()).decode()
        if config.get("ntfy_actions"):
            headers["Actions"] = self.encode_rfc2047(config["ntfy_actions"])
        response = requests.post(f"{(config.get('ntfy_url') or 'https://ntfy.sh').rstrip('/')}/{config['ntfy_topic']}", data=content.encode(), headers=headers, timeout=15)
        return ok_detail(self.label) if response.status_code == 200 else response_error(self.label, response.text)


class WxPusherSender(ChannelSender):
    type_name = "wxpusher"
    label = "WxPusher"
    config_schema = {"wxpusher_app_token": field("appToken", required=True, secret=True), "wxpusher_topic_ids": field("Topic IDs，多个用 ; 分隔"), "wxpusher_uids": field("UIDs，多个用 ; 分隔")}

    def send(self, *, title: str, content: str, config: dict[str, Any], target: str | None) -> tuple[bool, str]:
        topic_ids = [int(item) for item in split_semicolon(config.get("wxpusher_topic_ids"))]
        uids = split_semicolon(config.get("wxpusher_uids"))
        if not topic_ids and not uids:
            raise ValueError("wxpusher_topic_ids 和 wxpusher_uids 至少配置一个")
        data = requests.post("https://wxpusher.zjiecode.com/api/send/message", json={"appToken": config["wxpusher_app_token"], "content": f"<h1>{title}</h1><br/><div style='white-space: pre-wrap;'>{content}</div>", "summary": title, "contentType": 2, "topicIds": topic_ids, "uids": uids, "verifyPayType": 0}, timeout=15).json()
        return ok_detail(self.label) if data.get("code") == 1000 else response_error(self.label, data)


class ChannelRegistry:
    def __init__(self) -> None:
        senders: list[ChannelSender] = [
            BarkSender(), ConsoleSender(), DingtalkSender(), FeishuSender(), GoCqHttpSender(),
            GotifySender(), IGotSender(), ServerChanSender(), PushDeerSender(), SynologyChatSender(),
            PushPlusSender(), WePlusSender(), QmsgSender(), WeComAppSender(), WeComBotSender(),
            TelegramSender(), AibotkSender(), EmailSender(), PushMeSender(), ChronocatSender(),
            WebhookSender(), NtfySender(), WxPusherSender(),
        ]
        self._senders = {sender.type_name: sender for sender in senders}

    def get(self, type_name: str) -> ChannelSender:
        if type_name not in self._senders:
            raise KeyError(f"不支持的渠道类型: {type_name}")
        return self._senders[type_name]

    def meta(self) -> list[dict[str, Any]]:
        return [
            {
                "type": sender.type_name,
                "label": sender.label,
                "target_mode": sender.target_mode,
                "target_label": sender.target_label,
                "config_schema": sender.config_schema,
            }
            for sender in self._senders.values()
        ]

    def validate(self, type_name: str, config: dict[str, Any]) -> dict[str, Any]:
        return self.get(type_name).validate_config(config)


registry = ChannelRegistry()
