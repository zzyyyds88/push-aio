from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .core.db import Base


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    default_target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # 备用通道组：当前通道发送失败时，按列表顺序尝试这些通道（id 列表）
    backup_channel_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # 是否为紧急通道：normal 请求全失败后升级、emergency 请求直接并发走这里
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # 通道优先级，数字越小越先尝试；用于同组内排序
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # 同一次 /api/notify 调用的所有尝试共享一个 request_id（UUID）
    request_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    channel_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # 本条日志对应的角色：primary(主) / backup(备) / emergency(紧急)
    role: Mapped[str] = mapped_column(String(20), default="primary", nullable=False)
    # 如果是 backup/emergency，记录它替代的原始主通道 id
    original_channel_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    target: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # 错误分类：none/rate_limit/auth/config/network/channel_error
    # 由各渠道 SendResult.error_kind 写入；dispatcher 据此决定切换策略
    error_kind: Mapped[str] = mapped_column(String(20), default="none", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
