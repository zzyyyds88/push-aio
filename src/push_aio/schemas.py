from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ChannelType = str
DeliveryRole = Literal["primary", "backup", "emergency"]
# 错误分类：与 services/channels.py 中 ErrorKind 保持一致
# none=成功 / rate_limit=限流 / auth=认证失败 / config=配置错误 / network=网络异常 / channel_error=业务错误
ErrorKind = Literal["none", "rate_limit", "auth", "config", "network", "channel_error"]


class BarkConfig(BaseModel):
    bark_base_url: str = Field(..., description="完整 Bark 地址，通常已内含设备码")
    bark_group: str | None = None
    bark_sound: str | None = None
    bark_icon: str | None = None
    bark_level: str | None = None
    bark_url: str | None = None
    bark_archive: str | None = None


class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int = 465
    use_ssl: bool = True
    email: str
    auth_code: str
    from_name: str = "push-aio"


class ChannelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: ChannelType
    enabled: bool = True
    default_target: str | None = Field(default=None, max_length=255)
    config: dict[str, Any]
    is_emergency: bool = False
    # 发送顺序：数字越小越先尝试。主通道组（is_emergency=False）和紧急通道组（is_emergency=True）
    # 各自独立按 priority 升序排列。前端通过上移/下移按钮调整，无需手填。
    # 新建渠道时由后端自动追加到所在组末尾，前端创建表单不展示此字段。
    priority: int | None = Field(default=None, ge=0, le=1000)


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    enabled: bool | None = None
    default_target: str | None = Field(default=None, max_length=255)
    config: dict[str, Any] | None = None
    is_emergency: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=1000)


class ChannelOut(ChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ChannelMeta(BaseModel):
    type: ChannelType
    label: str
    target_mode: Literal["embedded", "external"]
    target_label: str | None = None
    config_schema: dict[str, Any]


class ChannelStatusOut(BaseModel):
    id: int
    name: str
    type: ChannelType
    label: str
    enabled: bool
    configured: bool
    online: bool
    target_mode: Literal["embedded", "external"]
    default_target: str | None = None
    is_emergency: bool = False
    priority: int = 100
    detail: str


class PlatformStatusOut(BaseModel):
    ok: bool
    supported_count: int
    configured_count: int
    enabled_count: int
    online_count: int
    emergency_count: int
    supported_types: list[ChannelMeta]
    channels: list[ChannelStatusOut]


class NotifyAttachment(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    content_base64: str = Field(..., min_length=1)
    content_type: str = "application/octet-stream"
    inline_content_id: str | None = None


class NotifyRequest(BaseModel):
    """外部调用接口的请求体。

    外部调用方可选指定 channel_type（渠道类型，如 "dingtalk_bot"、"bark"），
    系统在该类型的启用渠道里按 priority 逐个尝试 → 全失败升级全局紧急渠道。
    不传 channel_type 则走所有渠道全局调度（兜底）。
    严格模式：传任何额外字段都会被拒绝（422）。
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: Literal["plain", "html", "markdown"] = "plain"
    attachments: list[NotifyAttachment] | None = None
    # 可选：指定渠道类型（如 "dingtalk_bot"）。不传则走所有渠道全局调度。
    # 外部程序只需知道"我要钉钉推送"，不需知道具体渠道 ID。
    channel_type: str | None = Field(default=None, max_length=50)


class ChangeKeyRequest(BaseModel):
    """修改 API Key 的请求体。"""

    model_config = ConfigDict(extra="forbid")

    new_key: str = Field(..., min_length=12, max_length=256, description="新 Key，至少 12 位")


class AdminNotifyRequest(BaseModel):
    """WebUI 测试发送的请求体。

    管理员可在 WebUI 上选择渠道类型或具体渠道进行测试。
    不选时与外部 NotifyRequest 行为一致（走全自动调度）。
    """

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: Literal["plain", "html", "markdown"] = "plain"
    attachments: list[NotifyAttachment] | None = None
    # 可选：指定渠道类型（如 "dingtalk_bot"），在该类型启用渠道里走调度
    channel_type: str | None = Field(default=None, max_length=50)
    # 可选：只测试指定渠道（空则走全自动调度）
    channel_ids: list[int] | None = None


class NotifyChannelResult(BaseModel):
    channel_id: int
    channel_name: str
    channel_type: ChannelType
    success: bool
    target: str | None = None
    detail: str
    role: DeliveryRole = "primary"
    # 如果是 backup/emergency，记录它替代的原始主通道 id
    original_channel_id: int | None = None
    # 错误分类：success=True 时为 "none"；失败时为具体类型，前端用于展示中文标签
    error_kind: ErrorKind = "none"


class NotifyResponse(BaseModel):
    success: bool
    request_id: str
    # 主通道组按 priority 升序逐个尝试的记录（任一成功即停止）
    main_attempts: list[NotifyChannelResult] = Field(default_factory=list)
    # 主通道全失败后，紧急通道组按 priority 升序逐个尝试的记录
    emergency_attempts: list[NotifyChannelResult] = Field(default_factory=list)
    escalated: bool = False
    results: list[NotifyChannelResult]  # 扁平结果（main + emergency）


class DeliveryLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str | None
    channel_id: int | None
    channel_name: str
    channel_type: str
    role: str
    original_channel_id: int | None
    success: bool
    target: str | None
    title: str
    detail: str
    error_kind: str = "none"
    created_at: datetime
