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
from dataclasses import dataclass
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Any, Literal

import requests


# ==================== 错误分类 ====================
# success=True 时 error_kind="none"
# 失败时按原因分类，dispatcher 据此决定是否重试 / 是否立即切换
#   rate_limit:    被限流（HTTP 429 / "频率过高" / "too many requests" 等）→ 不重试，立即切备用
#   auth:          认证失败（token 错 / 401 / 403）→ 不重试，立即切备用
#   config:        配置错误（缺必填 / 格式错）→ 不重试，立即切备用（需用户改配置）
#   network:       网络异常（Timeout / ConnectionError）→ 重试 1 次后切备用
#   channel_error: 渠道返回业务错误（余额不足 / 用户不存在 / 内容违规等）→ 不重试，立即切备用
ErrorKind = Literal["none", "rate_limit", "auth", "config", "network", "channel_error"]


@dataclass
class SendResult:
    """渠道发送统一返回结构。"""
    success: bool
    detail: str
    error_kind: ErrorKind = "none"

    @classmethod
    def ok(cls, detail: str) -> "SendResult":
        return cls(True, detail, "none")

    @classmethod
    def fail(cls, detail: str, error_kind: ErrorKind = "channel_error") -> "SendResult":
        return cls(False, detail, error_kind)


FieldSchema = dict[str, Any]


def field(label: str, *, required: bool = False, secret: bool = False, kind: str = "text", default: Any = None, advanced: bool = False) -> FieldSchema:
    """定义渠道配置字段。

    advanced=True 表示高级选项（如原始 payload、代理、特殊操作），
    前端会折叠到「高级配置」里；其他字段（含可选）都直接展示，
    因为个人推送中心的常用配置（签名密钥、URL、行为开关等）不应被折叠。
    """
    return {"label": label, "required": required, "secret": secret, "type": kind, "default": default, "advanced": advanced}


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


# ==================== 通用错误识别 ====================
# 关键字命中即判为限流（不区分大小写）
_RATE_LIMIT_KEYWORDS = (
    "rate limit", "rate_limit", "ratelimit",
    "too many requests", "too_many_requests",
    "频率", "限流", "过于频繁", "请求过于频繁", "发送过于频繁",
    "频率过高", "操作太频繁", "超出限制", "exceeded",
    "quota", "throttl",
)

# 认证失败关键字
_AUTH_KEYWORDS = (
    "invalid token", "invalid_token", "token is invalid", "token invalid",
    "authentication failed", "unauthorized", "forbidden",
    "授权码错误", "认证失败", "鉴权失败", "令牌无效", "key 无效", "key无效",
    "access denied", "permission denied",
)


def classify_text(text: str) -> ErrorKind:
    """根据返回文本识别错误类型（限流/认证/其他业务错误）。"""
    lower = str(text).lower()
    for kw in _RATE_LIMIT_KEYWORDS:
        if kw in lower:
            return "rate_limit"
    for kw in _AUTH_KEYWORDS:
        if kw in lower:
            return "auth"
    return "channel_error"


def classify_response(*, status_code: int | None = None, body: Any = None) -> ErrorKind:
    """根据 HTTP 状态码 + 响应体识别错误类型。

    - 429 → rate_limit（被限流，立即切备用）
    - 401/403 → auth（认证失败，立即切备用）
    - 400 → config（请求格式错，需用户改配置）
    - 5xx → network（服务端临时故障，可重试）
    - 其他状态码 + body 关键字命中 → 对应类型
    - 都不命中 → channel_error
    """
    if status_code == 429:
        return "rate_limit"
    if status_code in (401, 403):
        return "auth"
    if status_code == 400:
        return "config"
    if status_code is not None and 500 <= status_code < 600:
        return "network"
    body_text = json.dumps(body, ensure_ascii=False) if not isinstance(body, str) else body
    return classify_text(body_text)


def ok_detail(name: str) -> SendResult:
    return SendResult.ok(f"{name} 推送成功")


def response_error(name: str, data: Any, *, status_code: int | None = None) -> SendResult:
    error_kind = classify_response(status_code=status_code, body=data)
    return SendResult.fail(f"{name} 返回异常: {data}", error_kind)


class ChannelSender(ABC):
    type_name: str
    label: str
    target_mode = "embedded"
    target_label: str | None = None
    # 渠道配置：只保留连接凭证（token、url、device_key 等），不含内容字段
    config_schema: dict[str, FieldSchema] = {}
    # 渠道支持的格式：调用方传 plain/markdown/html，兼容层自动适配
    # 基于官方文档核实，文档存放在 docs/channel-docs/ 目录
    supported_formats: list[str] = ["plain"]
    # 请求格式不支持时降级到的偏好格式
    preferred_format: str = "plain"
    # 渠道支持的内容字段 schema（透传字段），key 为渠道原生 API 字段名
    # 调用方通过 /api/notify 的 extra 参数传递，兼容层透传给渠道
    # 内容字段不固化在渠道配置里，每次调用按消息传递，与原推送机制一致
    extra_schema: dict[str, FieldSchema] = {}
    # 各渠道可覆盖：自己的 errcode → error_kind 映射
    # 例如钉钉 130101 = 限流，310000 = 鉴权失败
    errcode_map: dict[int, ErrorKind] = {}

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

    def classify_errcode(self, errcode: int | None) -> ErrorKind | None:
        """子类覆盖 errcode_map 后，按业务 errcode 识别错误类型。"""
        if errcode is None:
            return None
        return self.errcode_map.get(errcode)

    @abstractmethod
    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        """发送消息。

        Args:
            content_format: 兼容层转换后的格式 (plain/markdown/html)，
                           渠道按此格式构造自己的 payload。
                           兼容层已保证 content_format 在 supported_formats 内。
            extra: 调用方传递的渠道特有内容字段（key 为渠道原生 API 字段名），
                   渠道按自身 API 透传到 payload/headers。None 或空表示不传。
        """
        raise NotImplementedError


class ConsoleSender(ChannelSender):
    type_name = "console"
    label = "控制台"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        return SendResult.ok(f"{title}\n\n{content}")


class BarkSender(ChannelSender):
    type_name = "bark"
    label = "Bark"
    # bark-server 官方 API V2 字段表里没有 markdown，但服务端会透传未知字段给 APNs，
    # Bark iOS 客户端识别 markdown 字段后用 MarkdownView 渲染（见 docs/channel-docs/bark-server.md）。
    # 因此保留 markdown 能力：iOS 用户用 content_type=markdown 可获得富文本渲染。
    supported_formats = ["plain", "markdown"]
    preferred_format = "plain"
    # 渠道配置只保留连接凭证：base_url、device_key、device_keys
    config_schema = {
        "bark_base_url": field("Bark 推送地址（如 https://api.day.app/你的设备码），或仅填设备码", required=True),
        "bark_device_key": field("附加设备 key（单个）"),
        "bark_device_keys": field("附加设备 key（多个，英文逗号分隔）"),
    }
    # 内容字段全部走 extra，key 用 Bark 原生 API 字段名（见 docs/channel-docs/bark-server.md）
    # 调用方传 extra={"subtitle":"...","group":"...","sound":"..."} 即可透传
    extra_schema = {
        "subtitle": field("副标题"),
        "group": field("分组"),
        "sound": field("声音"),
        "icon": field("图标 URL"),
        "level": field("时效等级（active/timeSensitive/passive）"),
        "url": field("点击跳转 URL"),
        "isArchive": field("是否存档", kind="boolean"),
        "badge": field("角标数字", kind="number"),
        "volume": field("重要提醒音量 0-10", kind="number"),
        "autoCopy": field("自动复制", kind="boolean"),
        "copy": field("复制内容"),
        "call": field("重复提醒", kind="boolean"),
        "image": field("图片 URL"),
        "ciphertext": field("密文", advanced=True),
        "action": field("操作参数", advanced=True),
        "id": field("消息 ID", advanced=True),
        "delete": field("删除消息 ID", advanced=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        url = config["bark_base_url"]
        if url.startswith("http") and config.get("bark_device_key") and not url.rstrip("/").endswith("/push"):
            parsed = urllib.parse.urlparse(url)
            url = f"{parsed.scheme}://{parsed.netloc}/push"
        elif not url.startswith("http"):
            url = f"https://api.day.app/{url}"
        payload = {"title": title}
        if content_format == "markdown":
            payload["markdown"] = content
        else:
            payload["body"] = content
        # 连接凭证：device_key / device_keys 从 config 读
        if config.get("bark_device_keys"):
            payload["device_keys"] = [
                item.strip() for item in str(config["bark_device_keys"]).split(",") if item.strip()
            ]
        if config.get("bark_device_key"):
            payload["device_key"] = config["bark_device_key"]
        # 内容字段：仅透传 extra_schema 声明的字段（白名单）
        # 防止调用方通过 extra 传 device_key/device_keys 覆盖连接凭证发给第三方
        if extra:
            for key in self.extra_schema:
                value = extra.get(key)
                if value not in (None, ""):
                    payload[key] = value
        response = requests.post(url, json=payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("code") == 200:
            return ok_detail(self.label)
        # Bark 自部署服务常见错误：400 设备 key 无效 / 429 限流
        return response_error(self.label, data, status_code=response.status_code)


class DingtalkSender(ChannelSender):
    type_name = "dingtalk_bot"
    label = "钉钉机器人"
    supported_formats = ["plain", "markdown"]
    preferred_format = "plain"
    # 钉钉官方错误码（https://open.dingtalk.com/document/orgapp/custom-robots-send-group-messages）
    # 限流：每机器人每分钟 20 条，超限限流 10 分钟，返回 410100
    errcode_map = {
        410100: "rate_limit",   # 发送速度太快而限流（真正的限流码）
        90030: "rate_limit",    # webhook 调用次数达到上限（每日上限）
        400101: "auth",         # access_token 不存在
        88: "auth",             # access_token is blank
        310000: "config",       # 安全校验失败：关键词未匹配 / 签名不匹配 / IP不在白名单 / timestamp无效
        400102: "channel_error",  # 机器人已停用
        400013: "channel_error",  # 群已被解散
    }
    config_schema = {
        "dd_bot_token": field("机器人 Webhook 的 access_token", required=True, secret=True),
        "dd_bot_secret": field("加签密钥（以 SEC 开头，启用加签安全设置时必填）", secret=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        # 签名查询串（timestamp & sign），与 extra（透传内容字段）分开命名，避免覆盖参数
        sign_query = ""
        if config.get("dd_bot_secret"):
            timestamp = str(round(time.time() * 1000))
            sign = hmac.new(
                config["dd_bot_secret"].encode(),
                f"{timestamp}\n{config['dd_bot_secret']}".encode(),
                digestmod=hashlib.sha256,
            ).digest()
            sign_query = f"&timestamp={timestamp}&sign={urllib.parse.quote_plus(base64.b64encode(sign))}"
        url = f"https://oapi.dingtalk.com/robot/send?access_token={config['dd_bot_token']}{sign_query}"
        # 消息类型由发送时的 content_format 决定，不固化在渠道配置里（与 Bark/ntfy 等渠道一致）
        if content_format == "markdown":
            payload = {"msgtype": "markdown", "markdown": {"title": title, "text": content}}
        else:
            payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
        response = requests.post(url, json=payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("errcode") == 0:
            return ok_detail(self.label)
        # 优先用 errcode_map
        errcode = data.get("errcode") if isinstance(data, dict) else None
        kind = self.classify_errcode(errcode) or classify_response(status_code=response.status_code, body=data)
        return SendResult.fail(f"{self.label} 返回异常: {data}", kind)


class FeishuSender(ChannelSender):
    type_name = "feishu_bot"
    label = "飞书/Lark 机器人"
    supported_formats = ["plain"]
    preferred_format = "plain"
    # 飞书自定义机器人 webhook 错误码（https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot）
    # 注意：webhook 机器人与 Open API 错误码完全不同，9999166x 是 Open API 码 webhook 不返回
    # 限流：单租户单机器人 100 次/分钟 + 5 次/秒
    errcode_map = {
        11232: "rate_limit",  # create message service trigger rate limit
        11247: "rate_limit",  # internal send message trigger rate limit
        19021: "auth",        # 签名不匹配
        19022: "auth",        # IP 不在白名单
        19024: "auth",        # 关键词未匹配
        9499: "config",       # 请求体格式错误（Bad Request）
    }
    config_schema = {
        "fskey": field("Webhook 地址后半段 key 或完整 URL", required=True, secret=True),
        "fssecret": field("加签密钥（启用签名校验时必填）", secret=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        url = config["fskey"] if config["fskey"].startswith("http") else f"https://open.feishu.cn/open-apis/bot/v2/hook/{config['fskey']}"
        # 飞书 webhook 个人自用场景统一用 text 类型发送 title + content
        payload = {"msg_type": "text", "content": {"text": f"{title}\n\n{content}"}}
        if config.get("fssecret"):
            timestamp = str(int(time.time()))
            sign = hmac.new(f"{timestamp}\n{config['fssecret']}".encode(), digestmod=hashlib.sha256).digest()
            payload.update({"timestamp": timestamp, "sign": base64.b64encode(sign).decode()})
        response = requests.post(url, json=payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and (data.get("StatusCode") == 0 or data.get("code") == 0):
            return ok_detail(self.label)
        code = data.get("code") if isinstance(data, dict) else None
        kind = self.classify_errcode(code) or classify_response(status_code=response.status_code, body=data)
        return SendResult.fail(f"{self.label} 返回异常: {data}", kind)


class GoCqHttpSender(ChannelSender):
    type_name = "go_cqhttp"
    label = "go-cqhttp"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {
        "gobot_url": field("接口 URL", required=True),
        "gobot_qq": field("目标参数，如 user_id=10000 或 group_id=10000", required=True),
        "gobot_token": field("access_token", secret=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        params = {"message": f"标题:{title}\n内容:{content}"}
        if config.get("gobot_token"):
            params["access_token"] = config["gobot_token"]
        url = f"{config['gobot_url']}?{config['gobot_qq']}"
        response = requests.get(url, params=params, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and (data.get("status") == "ok" or data.get("retcode") == 0):
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class GotifySender(ChannelSender):
    type_name = "gotify"
    label = "Gotify"
    supported_formats = ["plain", "markdown", "html"]
    preferred_format = "plain"
    config_schema = {
        "gotify_url": field("Gotify 地址", required=True),
        "gotify_token": field("应用 token", required=True, secret=True),
    }
    # 内容字段走 extra（key 用 Gotify 原生 API 字段名）
    extra_schema = {
        "priority": field("优先级", kind="number", default=0),
        "extras": field("extras JSON 对象", advanced=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        payload = {"title": title, "message": content, "priority": 0}
        extras: dict[str, Any] = {}
        if extra:
            if extra.get("priority") is not None:
                payload["priority"] = extra["priority"]
            if extra.get("extras"):
                extras = parse_json_value(extra["extras"]) or {}
        display_content_type = {"markdown": "text/markdown", "html": "text/html", "plain": "text/plain"}.get(content_format, "text/plain")
        extras.setdefault("client::display", {})["content_type"] = display_content_type
        payload["extras"] = extras
        response = requests.post(f"{config['gotify_url'].rstrip('/')}/message", params={"token": config["gotify_token"]}, json=payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("id"):
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class IGotSender(ChannelSender):
    type_name = "igot"
    label = "iGot"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {"igot_push_key": field("iGot push key", required=True, secret=True)}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        response = requests.post(f"https://push.hellyw.com/{config['igot_push_key']}", data={"title": title, "content": content}, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("ret") == 0:
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class ServerChanSender(ChannelSender):
    type_name = "server_chan"
    label = "Server 酱"
    supported_formats = ["plain", "markdown"]
    preferred_format = "markdown"
    config_schema = {"push_key": field("SendKey", required=True, secret=True)}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        match = re.match(r"sctp(\d+)t", config["push_key"])
        url = f"https://{match.group(1)}.push.ft07.com/send/{config['push_key']}.send" if match else f"https://sctapi.ftqq.com/{config['push_key']}.send"
        response = requests.post(url, data={"text": title, "desp": content.replace("\n", "\n\n")}, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and (data.get("errno") == 0 or data.get("code") == 0):
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class PushDeerSender(ChannelSender):
    type_name = "pushdeer"
    label = "PushDeer"
    supported_formats = ["plain", "markdown"]
    preferred_format = "plain"
    config_schema = {
        "deer_key": field("PushDeer key", required=True, secret=True),
        "deer_url": field("自定义 API URL"),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        url = config.get("deer_url") or "https://api2.pushdeer.com/message/push"
        if content_format == "markdown":
            data_payload = {"text": title, "desp": content, "type": "markdown", "pushkey": config["deer_key"]}
        else:
            data_payload = {"text": title, "desp": f"{title}\n\n{content}", "type": "text", "pushkey": config["deer_key"]}
        response = requests.post(url, data=data_payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("content", {}).get("result"):
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class SynologyChatSender(ChannelSender):
    type_name = "synology_chat"
    label = "Synology Chat"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {"chat_url": field("Synology Chat 的 Webhook URL", required=True), "chat_token": field("Token（URL 已包含则可留空）", secret=True)}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        url = config["chat_url"] + config.get("chat_token", "")
        response = requests.post(url, data="payload=" + json.dumps({"text": title + "\n" + content}), timeout=15)
        data = json_or_text(response)
        if response.status_code == 200:
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class PushPlusSender(ChannelSender):
    type_name = "pushplus"
    label = "PushPlus"
    supported_formats = ["plain", "html", "markdown"]
    preferred_format = "html"
    # PushPlus 官方返回码（https://www.pushplus.plus/doc/guide/code.html）
    # 限流：非会员每日 1000 次，触发 900 后账号级封禁 2~7 天
    # 注意：901/902 在官方文档中不存在，是历史误录，已删除
    errcode_map = {
        401: "auth",           # 请求未授权（开放接口未启用）
        403: "auth",           # 请求 IP 未授权
        500: "network",        # 系统异常（可重试）
        600: "channel_error",  # 数据异常
        888: "channel_error",  # 积分不足
        900: "rate_limit",     # 用户账号使用受限（请求次数过多）
        903: "auth",           # 无效的用户令牌
        905: "config",         # 账户未实名认证
        999: "channel_error",  # 服务端验证错误
    }
    config_schema = {
        "push_plus_token": field("用户令牌", required=True, secret=True),
    }
    # 内容字段走 extra（key 用 PushPlus 原生 API 字段名）
    # 注意：to 字段（好友令牌/企业微信用户 ID）已移除——个人推送中心不允许发给第三方
    extra_schema = {
        "channel": field("渠道（wechat/webhook/cp/mail等，默认 wechat）"),
        "topic": field("群组编码"),
        "webhook": field("Webhook 编码", advanced=True),
        "callbackUrl": field("回调 URL", advanced=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        template = {"html": "html", "markdown": "markdown", "plain": "txt"}.get(content_format, "html")
        body: dict[str, Any] = {
            "token": config["push_plus_token"], "title": title, "content": content,
            "template": template, "channel": "wechat",
        }
        if extra:
            for key in ("channel", "topic", "webhook", "callbackUrl"):
                if extra.get(key) not in (None, ""):
                    body[key] = extra[key]
        response = requests.post("https://www.pushplus.plus/send", json=body, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("code") == 200:
            return ok_detail(self.label)
        code = data.get("code") if isinstance(data, dict) else None
        kind = self.classify_errcode(code) or classify_response(status_code=response.status_code, body=data)
        return SendResult.fail(f"{self.label} 返回异常: {data}", kind)


class WePlusSender(ChannelSender):
    type_name = "weplus_bot"
    label = "微加机器人"
    supported_formats = ["plain", "html"]
    preferred_format = "html"
    config_schema = {
        "we_plus_bot_token": field("用户令牌", required=True, secret=True),
        "we_plus_bot_version": field("版本", default="pro", advanced=True),
    }
    # receiver 字段已移除——个人推送中心不允许发给第三方

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        template = "html" if content_format == "html" else "txt"
        body: dict[str, Any] = {"token": config["we_plus_bot_token"], "title": title, "content": content, "template": template, "version": config.get("we_plus_bot_version", "pro")}
        response = requests.post("https://www.weplusbot.com/send", json=body, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("code") == 200:
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class QmsgSender(ChannelSender):
    type_name = "qmsg"
    label = "Qmsg 酱"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {"qmsg_key": field("QMSG 推送 KEY", required=True, secret=True), "qmsg_type": field("推送类型（如 send）", required=True)}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        response = requests.post(f"https://qmsg.zendee.cn/{config['qmsg_type']}/{config['qmsg_key']}", params={"msg": f"{title}\n\n{content.replace('----', '-')}"}, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("code") == 0:
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class WeComBotSender(ChannelSender):
    type_name = "wecom_bot"
    label = "企业微信机器人"
    supported_formats = ["plain", "markdown"]
    preferred_format = "plain"
    # 企业微信官方错误码（https://developer.work.weixin.qq.com/document/path/90313）
    # 限流：每个 webhook 地址每分钟 20 条
    # 注意：45100/93000/93001 在官方文档中不存在，是历史误录，已删除
    errcode_map = {
        45009: "rate_limit",   # 接口调用超过限制
        45033: "rate_limit",   # 接口并发调用超过限制
        42001: "auth",         # access_token 已过期
        40014: "auth",         # 不合法的 access_token
        41001: "config",       # 缺少 access_token 参数
        41004: "config",       # 缺少 secret 参数
    }
    config_schema = {
        "qywx_key": field("机器人 Webhook key", required=True, secret=True),
        "qywx_origin": field("企业微信 API Origin", default="https://qyapi.weixin.qq.com"),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        origin = config.get("qywx_origin") or "https://qyapi.weixin.qq.com"
        # 消息类型由发送时的 content_format 决定，不固化在渠道配置里（与钉钉一致）
        if content_format == "markdown":
            payload = {"msgtype": "markdown", "markdown": {"content": f"## {title}\n\n{content}"}}
        else:
            payload = {"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}}
        response = requests.post(f"{origin}/cgi-bin/webhook/send?key={config['qywx_key']}", json=payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("errcode") == 0:
            return ok_detail(self.label)
        errcode = data.get("errcode") if isinstance(data, dict) else None
        kind = self.classify_errcode(errcode) or classify_response(status_code=response.status_code, body=data)
        return SendResult.fail(f"{self.label} 返回异常: {data}", kind)


class WeComAppSender(ChannelSender):
    type_name = "wecom_app"
    label = "企业微信应用"
    supported_formats = ["plain", "markdown"]
    preferred_format = "plain"
    errcode_map = {
        45009: "rate_limit",   # 接口调用超过限制
        45033: "rate_limit",   # 接口并发调用超过限制
        42001: "auth",         # access_token 已过期
        40014: "auth",         # 不合法的 access_token
        41001: "config",       # 缺少 access_token 参数
    }
    config_schema = {"qywx_am": field("企业微信应用凭证，按顺序：corpid,corpsecret,touser,agentid[,media_id]", required=True, secret=True), "qywx_origin": field("企业微信 API Origin", default="https://qyapi.weixin.qq.com")}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        parts = [item.strip() for item in config["qywx_am"].split(",")]
        if len(parts) not in (4, 5):
            raise ValueError("qywx_am 格式必须为 corpid,corpsecret,touser,agentid[,media_id]")
        corpid, corpsecret, touser, agentid = parts[:4]
        media_id = parts[4] if len(parts) == 5 else ""
        origin = config.get("qywx_origin") or "https://qyapi.weixin.qq.com"
        token_resp = requests.post(f"{origin}/cgi-bin/gettoken", params={"corpid": corpid, "corpsecret": corpsecret}, timeout=15).json()
        token = token_resp.get("access_token")
        if not token:
            kind = self.classify_errcode(token_resp.get("errcode")) or "auth"
            return SendResult.fail(f"{self.label} 获取 access_token 失败: {token_resp}", kind)
        payload: dict[str, Any] = {"touser": touser, "agentid": agentid, "safe": "0"}
        if media_id:
            payload.update({"msgtype": "mpnews", "mpnews": {"articles": [{"title": title, "thumb_media_id": media_id, "author": "PushHub", "content_source_url": "", "content": content.replace("\n", "<br/>"), "digest": content}]}})
        elif content_format == "markdown":
            payload.update({"msgtype": "markdown", "markdown": {"content": f"## {title}\n\n{content}"}})
        else:
            payload.update({"msgtype": "text", "text": {"content": f"{title}\n\n{content}"}})
        response = requests.post(f"{origin}/cgi-bin/message/send?access_token={token}", json=payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and (data.get("errcode") == 0 or data.get("errmsg") == "ok"):
            return ok_detail(self.label)
        errcode = data.get("errcode") if isinstance(data, dict) else None
        kind = self.classify_errcode(errcode) or classify_response(status_code=response.status_code, body=data)
        return SendResult.fail(f"{self.label} 返回异常: {data}", kind)


class TelegramSender(ChannelSender):
    type_name = "telegram_bot"
    label = "Telegram Bot"
    supported_formats = ["plain", "markdown", "html"]
    preferred_format = "markdown"
    # Telegram error_code: 429 = 限流；401 = token无效；403 = forbidden
    errcode_map = {
        429: "rate_limit",
        401: "auth",
        403: "auth",
    }
    # 渠道配置只保留连接凭证 + 代理配置
    config_schema = {
        "tg_bot_token": field("Bot token", required=True, secret=True),
        "tg_user_id": field("Chat ID", required=True),
        "tg_api_host": field("API Host"),
        "tg_proxy_auth": field("代理认证", advanced=True),
        "tg_proxy_host": field("代理 Host", advanced=True),
        "tg_proxy_port": field("代理 Port", advanced=True),
    }
    # 内容字段走 extra（key 用 Telegram 原生 API 字段名，见 docs/channel-docs/telegram-bot.md）
    extra_schema = {
        "disable_web_page_preview": field("禁用链接预览", kind="boolean"),
        "disable_notification": field("静默发送", kind="boolean"),
        "protect_content": field("保护内容", kind="boolean", advanced=True),
        "message_thread_id": field("话题 ID", kind="number", advanced=True),
        "reply_markup": field("reply_markup JSON", advanced=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        api_host = config.get("tg_api_host") or "https://api.telegram.org"
        proxies = None
        if config.get("tg_proxy_host") and config.get("tg_proxy_port"):
            auth = f"{config['tg_proxy_auth']}@" if config.get("tg_proxy_auth") else ""
            proxy = f"http://{auth}{config['tg_proxy_host']}:{config['tg_proxy_port']}"
            proxies = {"http": proxy, "https": proxy}
        parse_mode = {"markdown": "MarkdownV2", "html": "HTML"}.get(content_format)
        payload: dict[str, Any] = {
            "chat_id": str(config["tg_user_id"]),
            "text": f"{title}\n\n{content}",
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        # 内容字段从 extra 透传（key 用 Telegram 原生 API 字段名）
        if extra:
            for key in ("disable_web_page_preview", "disable_notification", "protect_content", "message_thread_id"):
                if extra.get(key) is not None:
                    payload[key] = extra[key]
            if extra.get("reply_markup"):
                payload["reply_markup"] = parse_json_value(extra["reply_markup"])
        response = requests.post(f"{api_host}/bot{config['tg_bot_token']}/sendMessage", json=payload, proxies=proxies, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("ok"):
            return ok_detail(self.label)
        # Telegram 用 error_code 字段
        code = data.get("error_code") if isinstance(data, dict) else None
        kind = self.classify_errcode(code) or classify_response(status_code=response.status_code, body=data)
        return SendResult.fail(f"{self.label} 返回异常: {data}", kind)


class AibotkSender(ChannelSender):
    type_name = "aibotk"
    label = "智能微秘书"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {"aibotk_key": field("API key", required=True, secret=True), "aibotk_type": field("推送目标类型（room=群聊 / contact=好友）", required=True), "aibotk_name": field("群名或好友昵称", required=True)}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        is_room = config["aibotk_type"] == "room"
        url = "https://api-bot.aibotk.com/openapi/v1/chat/room" if is_room else "https://api-bot.aibotk.com/openapi/v1/chat/contact"
        data_payload = {"apiKey": config["aibotk_key"], "message": {"type": 1, "content": f"【青龙快讯】\n\n{title}\n{content}"}}
        data_payload["roomName" if is_room else "name"] = config["aibotk_name"]
        response = requests.post(url, json=data_payload, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("code") == 0:
            return ok_detail(self.label)
        return response_error(self.label, data, status_code=response.status_code)


class EmailSender(ChannelSender):
    type_name = "email"
    label = "SMTP 邮件"
    supported_formats = ["plain", "html"]
    preferred_format = "plain"
    target_mode = "external"
    target_label = "收件邮箱，多个用英文分号分隔；不填则发给自己"
    config_schema = {
        "smtp_host": field("SMTP 主机地址", required=True),
        "smtp_port": field("SMTP 端口", kind="number", default=465),
        "use_ssl": field("启用 SSL", kind="boolean", default=True),
        "email": field("发件邮箱", required=True),
        "auth_code": field("SMTP 授权码（非邮箱密码）", required=True, secret=True),
        "from_name": field("发件人名称", default="PushHub"),
    }

    def validate_config(self, raw_config: dict[str, Any]) -> dict[str, Any]:
        config = dict(raw_config)
        if not config.get("smtp_host") and config.get("imap_host"):
            config["smtp_host"] = str(config["imap_host"]).replace("imap.", "smtp.", 1)
        return super().validate_config(config)

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        to_addrs = split_semicolon(target) or [config["email"]]
        content_type = "html" if content_format == "html" else "plain"
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
        message["From"] = formataddr((str(Header(config.get("from_name", "PushHub"), "utf-8")), config["email"]))
        message["To"] = ";".join(to_addrs)
        client = smtplib.SMTP_SSL(config["smtp_host"], config.get("smtp_port", 465), timeout=15) if parse_bool(config.get("use_ssl"), True) else smtplib.SMTP(config["smtp_host"], config.get("smtp_port", 25), timeout=15)
        try:
            if not parse_bool(config.get("use_ssl"), True):
                client.starttls()
            client.login(config["email"], config["auth_code"])
            client.sendmail(config["email"], to_addrs, message.as_string())
        except smtplib.SMTPAuthenticationError as exc:
            # 535 认证失败 / 535 授权码错误
            return SendResult.fail(f"{self.label} 认证失败: {exc}", "auth")
        except smtplib.SMTPConnectError as exc:
            return SendResult.fail(f"{self.label} 连接失败: {exc}", "network")
        except smtplib.SMTPServerDisconnected as exc:
            return SendResult.fail(f"{self.label} 服务器断开: {exc}", "network")
        except smtplib.SMTPResponseException as exc:
            # 4xx 临时错误（含限流），5xx 永久错误
            kind = "rate_limit" if 400 <= exc.smtp_code < 500 else "channel_error"
            return SendResult.fail(f"{self.label} 返回异常: {exc.smtp_code} {exc.smtp_error.decode(errors='ignore') if isinstance(exc.smtp_error, bytes) else exc.smtp_error}", kind)
        finally:
            try:
                client.quit()
            except Exception:
                pass
        return ok_detail(self.label)


class PushMeSender(ChannelSender):
    type_name = "pushme"
    label = "PushMe"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {"pushme_key": field("PushMe key", required=True, secret=True), "pushme_url": field("PushMe URL", default="https://push.i-i.me/")}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        response = requests.post(config.get("pushme_url") or "https://push.i-i.me/", data={"push_key": config["pushme_key"], "title": title, "content": content}, timeout=15)
        if response.status_code == 200 and response.text == "success":
            return ok_detail(self.label)
        return response_error(self.label, f"{response.status_code} {response.text}", status_code=response.status_code)


class ChronocatSender(ChannelSender):
    type_name = "chronocat"
    label = "Chronocat"
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {"chronocat_url": field("Chronocat 服务地址", required=True), "chronocat_qq": field("推送目标，如 user_id=10000 或 group_id=10000", required=True), "chronocat_token": field("访问 Token", required=True, secret=True)}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
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
                    return response_error(self.label, response.text, status_code=response.status_code)
                sent += 1
        return ok_detail(self.label) if sent else SendResult.fail("Chronocat 未匹配到 user_id 或 group_id", "config")


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
    supported_formats = ["plain"]
    preferred_format = "plain"
    config_schema = {
        "webhook_url": field("请求 URL，支持 $title/$content", required=True),
        "webhook_method": field("请求方法", required=True, default="POST"),
        "webhook_content_type": field("Content-Type", default="application/json"),
        "webhook_headers": field("请求头，每行 key: value", advanced=True),
        "webhook_body": field("请求体，支持 $title/$content", advanced=True),
    }

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        if "$title" not in config["webhook_url"] and "$title" not in config.get("webhook_body", ""):
            raise ValueError("URL 或 Body 中必须包含 $title")
        headers = parse_headers(config.get("webhook_headers"))
        if config.get("webhook_content_type"):
            headers.setdefault("Content-Type", config["webhook_content_type"])
        url = config["webhook_url"].replace("$title", urllib.parse.quote_plus(title)).replace("$content", urllib.parse.quote_plus(content))
        body = replace_vars(config.get("webhook_body", ""), title, content) if config.get("webhook_body") else None
        response = requests.request(config["webhook_method"].upper(), url, headers=headers, data=body, timeout=15)
        if 200 <= response.status_code < 300:
            return ok_detail(self.label)
        return response_error(self.label, f"{response.status_code} {response.text}", status_code=response.status_code)


class NtfySender(ChannelSender):
    type_name = "ntfy"
    label = "ntfy"
    supported_formats = ["plain", "markdown"]
    preferred_format = "plain"
    # 渠道配置只保留连接凭证
    config_schema = {
        "ntfy_url": field("ntfy 地址", default="https://ntfy.sh"),
        "ntfy_topic": field("Topic", required=True),
        "ntfy_token": field("Bearer token", secret=True),
        "ntfy_username": field("用户名"),
        "ntfy_password": field("密码", secret=True),
    }
    # 内容字段走 extra（key 用 ntfy 原生 API 字段名，见 docs/channel-docs/ntfy.md）
    # ntfy 的内容字段通过 HTTP header 传递，send 方法会映射到对应 header
    # 注意：email 字段已移除——个人推送中心不允许转发给第三方邮箱
    extra_schema = {
        "priority": field("优先级（1-5，默认 3）"),
        "tags": field("标签，多个用英文逗号分隔"),
        "click": field("点击 URL"),
        "attach": field("附件 URL"),
        "filename": field("附件文件名"),
        "actions": field("Actions", advanced=True),
        "delay": field("延迟发送", advanced=True),
    }

    @staticmethod
    def encode_rfc2047(text: str) -> str:
        return f"=?utf-8?B?{base64.b64encode(text.encode()).decode()}?="

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        headers = {"Title": self.encode_rfc2047(title), "Icon": "https://qn.whyour.cn/logo.png"}
        if content_format == "markdown":
            headers["Markdown"] = "yes"
        if config.get("ntfy_token"):
            headers["Authorization"] = "Bearer " + config["ntfy_token"]
        elif config.get("ntfy_username") and config.get("ntfy_password"):
            headers["Authorization"] = "Basic " + base64.b64encode(f"{config['ntfy_username']}:{config['ntfy_password']}".encode()).decode()
        # 内容字段从 extra 透传到 HTTP header（key 用 ntfy 原生 API 字段名）
        header_map = {
            "priority": "Priority",
            "tags": "Tags",
            "click": "Click",
            "attach": "Attach",
            "filename": "Filename",
            "delay": "Delay",
        }
        if extra:
            for key, header in header_map.items():
                if extra.get(key) not in (None, ""):
                    headers[header] = str(extra[key])
            if extra.get("actions"):
                headers["Actions"] = self.encode_rfc2047(extra["actions"])
        response = requests.post(f"{(config.get('ntfy_url') or 'https://ntfy.sh').rstrip('/')}/{config['ntfy_topic']}", data=content.encode(), headers=headers, timeout=15)
        if response.status_code == 200:
            return ok_detail(self.label)
        return response_error(self.label, response.text, status_code=response.status_code)


class WxPusherSender(ChannelSender):
    type_name = "wxpusher"
    label = "WxPusher"
    supported_formats = ["plain", "html", "markdown"]
    preferred_format = "html"
    # WxPusher 官方错误码（code: 1000 = 成功）
    errcode_map = {
        1001: "auth",          # appToken 无效或缺失
        1002: "config",        # content 为空
        1003: "config",        # 无有效 UID/TopicId
        1004: "auth",          # 应用不存在
        1005: "channel_error", # 服务器内部错误
    }
    config_schema = {"wxpusher_app_token": field("应用 appToken", required=True, secret=True), "wxpusher_topic_ids": field("Topic IDs，多个用 ; 分隔"), "wxpusher_uids": field("UIDs，多个用 ; 分隔")}

    def send(self, *, title: str, content: str, content_format: str, config: dict[str, Any], target: str | None, extra: dict[str, Any] | None = None) -> SendResult:
        topic_ids = [int(item) for item in split_semicolon(config.get("wxpusher_topic_ids"))]
        uids = split_semicolon(config.get("wxpusher_uids"))
        if not topic_ids and not uids:
            raise ValueError("wxpusher_topic_ids 和 wxpusher_uids 至少配置一个")
        if content_format == "markdown":
            content_body = f"## {title}\n\n{content}"
            content_type_num = 3
        elif content_format == "plain":
            content_body = f"{title}\n\n{content}"
            content_type_num = 1
        else:
            content_body = f"<h1>{title}</h1><br/><div style='white-space: pre-wrap;'>{content}</div>"
            content_type_num = 2
        response = requests.post("https://wxpusher.zjiecode.com/api/send/message", json={"appToken": config["wxpusher_app_token"], "content": content_body, "summary": title, "contentType": content_type_num, "topicIds": topic_ids, "uids": uids, "verifyPayType": 0}, timeout=15)
        try:
            data = response.json()
        except ValueError:
            data = response.text
        if isinstance(data, dict) and data.get("code") == 1000:
            return ok_detail(self.label)
        code = data.get("code") if isinstance(data, dict) else None
        kind = self.classify_errcode(code) or classify_response(status_code=response.status_code, body=data)
        return SendResult.fail(f"{self.label} 返回异常: {data}", kind)


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
                # 暴露给调用方：渠道支持的 content_type 列表 + 降级偏好
                # 调用方据此判断能否用 markdown/html 推送（如钉钉、企业微信支持 markdown）
                "supported_formats": list(sender.supported_formats),
                "preferred_format": sender.preferred_format,
                # 暴露给调用方：渠道支持的内容字段 schema（透传字段）
                # 调用方通过 /api/notify 的 extra 参数传递这些字段
                "extra_schema": sender.extra_schema,
            }
            for sender in self._senders.values()
        ]

    def validate(self, type_name: str, config: dict[str, Any]) -> dict[str, Any]:
        return self.get(type_name).validate_config(config)


registry = ChannelRegistry()
