from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


ChannelType = str
Priority = Literal["normal", "emergency"]
DeliveryRole = Literal["primary", "backup", "emergency"]


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
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    content_type: Literal["plain", "html", "markdown"] = "plain"
    # normal：常规发送，主链全失败后自动升级到紧急通道
    # emergency：紧急发送，主链与紧急通道并发触发
    priority: Priority = "normal"
    attachments: list[NotifyAttachment] | None = None
    channel_ids: list[int] | None = None
    channel_types: list[ChannelType] | None = None
    channel_names: list[str] | None = None
    target_overrides: dict[int, str] | None = None
    config_overrides: dict[int, dict[str, Any]] | None = None
    # True 时即便匹配到主通道也强制并发触发紧急通道
    force_emergency: bool = False


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


class NotifyChainGroup(BaseModel):
    """以一个主通道为根的整条尝试链路。"""
    primary: NotifyChannelResult
    backups: list[NotifyChannelResult] = Field(default_factory=list)
    success: bool
    final_role: DeliveryRole


class NotifyResponse(BaseModel):
    success: bool
    request_id: str
    priority: Priority
    chains: list[NotifyChainGroup]
    emergency_attempts: list[NotifyChannelResult] = Field(default_factory=list)
    escalated: bool = False
    results: list[NotifyChannelResult]  # 扁平结果，向后兼容


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
    created_at: datetime
