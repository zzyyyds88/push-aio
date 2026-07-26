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
    backup_channel_ids: list[int] = Field(default_factory=list)
    is_emergency: bool = False
    priority: int = Field(default=100, ge=0, le=1000)


class ChannelCreate(ChannelBase):
    pass


class ChannelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    enabled: bool | None = None
    default_target: str | None = Field(default=None, max_length=255)
    config: dict[str, Any] | None = None
    backup_channel_ids: list[int] | None = None
    is_emergency: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=1000)


class ChannelOut(ChannelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class BackupGroupUpdate(BaseModel):
    """单独更新某渠道的备用组，避免和渠道本体配置耦合。"""
    backup_channel_ids: list[int] = Field(default_factory=list)


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
    backup_channel_ids: list[int] = Field(default_factory=list)
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

    外部调用方只能传消息内容，不能选择渠道、不能指定优先级——
    调度策略由系统固定为：主通道 → 备用通道 → 全失败升级紧急通道。
    严格模式：传任何额外字段都会被拒绝（422）。
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: Literal["plain", "html", "markdown"] = "plain"
    attachments: list[NotifyAttachment] | None = None


class ChangeKeyRequest(BaseModel):
    """修改 API Key 的请求体。"""

    model_config = ConfigDict(extra="forbid")

    new_key: str = Field(..., min_length=12, max_length=256, description="新 Key，至少 12 位")


class AdminNotifyRequest(BaseModel):
    """WebUI 测试发送的请求体。

    管理员可在 WebUI 上选择特定渠道进行测试，方便排查单个渠道问题。
    不选渠道时与外部 NotifyRequest 行为一致（走全自动调度）。
    """

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: Literal["plain", "html", "markdown"] = "plain"
    attachments: list[NotifyAttachment] | None = None
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


class NotifyChainGroup(BaseModel):
    """以一个主通道为根的整条尝试链路。"""
    primary: NotifyChannelResult
    backups: list[NotifyChannelResult] = Field(default_factory=list)
    success: bool
    final_role: DeliveryRole


class NotifyResponse(BaseModel):
    success: bool
    request_id: str
    chains: list[NotifyChainGroup]
    emergency_attempts: list[NotifyChannelResult] = Field(default_factory=list)
    escalated: bool = False
    results: list[NotifyChannelResult]  # 扁平结果


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
