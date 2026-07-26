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
    # [已废弃 v0.5] 原"每个主通道独立备用组"模型，已改为全局有序列表调度
    # 字段保留仅为兼容旧库，代码不再读写；新建渠道默认空列表
    backup_channel_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    # 是否为紧急通道：同类型层级(主备用)全失败后自动升级到全局紧急层级
    is_emergency: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # 发送顺序：数字越小越先尝试。同类型层级(is_emergency=False)与全局紧急层级(is_emergency=True)
    # 各自独立按 priority 升序排列。前端通过上移/下移按钮调整，无需手填。
    # 注意：紧急层级实际是并发发送，priority 仅影响并发结果中 final_* 的取值顺序
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


class Setting(Base):
    """通用键值配置表：存放 API Key 等需要持久化到 DB 的配置。

    个人推送中心无需多用户多 Key，故用 key-value 结构最简实现。
    当前已用键：
      - api_key: WebUI 登录密码 + 外部调用 X-API-Key（同一把）
    """
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
