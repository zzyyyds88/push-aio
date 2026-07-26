from __future__ import annotations

import uuid
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Channel, DeliveryLog
from ..schemas import (
    AdminNotifyRequest,
    NotifyChannelResult,
    NotifyChainGroup,
    NotifyRequest,
    NotifyResponse,
)
from .channels import registry


# 视为瞬时异常：值得重试一次
_TRANSIENT_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
)


def _send_one(
    channel: Channel,
    payload: NotifyRequest | AdminNotifyRequest,
) -> tuple[bool, str, str | None]:
    """对单通道执行 1+1 重试发送，返回 (success, detail, target)。"""
    sender = registry.get(channel.type)
    target = channel.default_target
    config = dict(channel.config)
    config["_notify_content_type"] = payload.content_type
    if channel.type == "email":
        config["_content_type"] = payload.content_type
        config["_attachments"] = [
            attachment.model_dump() for attachment in (payload.attachments or [])
        ]

    last_error = "未知错误"
    for attempt in range(2):  # 首次 + 1 次瞬时重试
        try:
            config_validated = registry.validate(channel.type, config)
            success, detail = sender.send(
                title=payload.title,
                content=payload.content,
                config=config_validated,
                target=target,
            )
            return success, detail, target
        except _TRANSIENT_EXCEPTIONS as exc:
            last_error = f"网络异常: {exc}"
            continue
        except Exception as exc:
            return False, str(exc), target
    return False, last_error, target


def _attempt(
    channel: Channel,
    payload: NotifyRequest | AdminNotifyRequest,
    role: str,
    original_channel_id: int | None,
    db: Session,
    request_id: str,
    tried: dict[int, NotifyChannelResult],
) -> NotifyChannelResult:
    """对一个通道做一次完整尝试；同请求内已尝试的通道直接复用结果不重发。"""
    if channel.id in tried:
        cached = tried[channel.id]
        return NotifyChannelResult(
            channel_id=cached.channel_id,
            channel_name=cached.channel_name,
            channel_type=cached.channel_type,
            success=cached.success,
            target=cached.target,
            detail=f"复用本次请求已尝试结果：{cached.detail}",
            role=role,
            original_channel_id=original_channel_id,
        )

    success, detail, target = _send_one(channel, payload)

    db.add(
        DeliveryLog(
            request_id=request_id,
            channel_id=channel.id,
            channel_name=channel.name,
            channel_type=channel.type,
            role=role,
            original_channel_id=original_channel_id,
            success=success,
            target=target,
            title=payload.title,
            detail=detail,
        )
    )

    result = NotifyChannelResult(
        channel_id=channel.id,
        channel_name=channel.name,
        channel_type=channel.type,
        success=success,
        target=target,
        detail=detail,
        role=role,
        original_channel_id=original_channel_id,
    )
    tried[channel.id] = result
    return result


def _resolve_backup(channel: Channel, backup_id: int, db: Session) -> Channel | None:
    if backup_id == channel.id:
        return None
    backup = db.get(Channel, backup_id)
    if not backup or not backup.enabled:
        return None
    return backup


def dispatch(
    payload: NotifyRequest | AdminNotifyRequest,
    db: Session,
) -> NotifyResponse:
    """固定调度策略：主通道 → 备用通道 → 全失败升级紧急通道。

    外部调用方（NotifyRequest）和 WebUI 测试发送（AdminNotifyRequest）共用此函数。
    AdminNotifyRequest 可选传 channel_ids 限定测试范围，不传则对所有启用通道走完整调度。
    """
    request_id = str(uuid.uuid4())

    # 主通道：所有启用的非紧急通道（按 priority 升序）
    primary_query = select(Channel).where(
        Channel.enabled.is_(True),
        Channel.is_emergency.is_(False),
    )
    # AdminNotifyRequest 可限定测试渠道
    channel_ids = getattr(payload, "channel_ids", None)
    if channel_ids:
        primary_query = primary_query.where(Channel.id.in_(channel_ids))
    primary_channels = list(
        db.scalars(primary_query.order_by(Channel.priority.asc(), Channel.id.asc())).all()
    )

    # 紧急通道：仅在主链全失败时自动升级
    emergency_channels = list(
        db.scalars(
            select(Channel)
            .where(Channel.enabled.is_(True), Channel.is_emergency.is_(True))
            .order_by(Channel.priority.asc(), Channel.id.asc())
        ).all()
    )

    tried: dict[int, NotifyChannelResult] = {}
    chains: list[NotifyChainGroup] = []
    flat_results: list[NotifyChannelResult] = []

    # 主链路：每个主通道尝试 → 失败则按备用组顺序兜底
    for primary in primary_channels:
        primary_result = _attempt(
            primary, payload, "primary", None, db, request_id, tried
        )
        flat_results.append(primary_result)

        backups: list[NotifyChannelResult] = []
        if not primary_result.success:
            for backup_id in primary.backup_channel_ids or []:
                backup = _resolve_backup(primary, backup_id, db)
                if not backup:
                    continue
                backup_result = _attempt(
                    backup, payload, "backup", primary.id, db, request_id, tried
                )
                backups.append(backup_result)
                flat_results.append(backup_result)
                if backup_result.success:
                    break

        chain_success = primary_result.success or any(b.success for b in backups)
        if primary_result.success:
            final_role = "primary"
        elif any(b.success for b in backups):
            final_role = "backup"
        else:
            final_role = "primary"  # 链路失败时，记主通道角色
        chains.append(
            NotifyChainGroup(
                primary=primary_result,
                backups=backups,
                success=chain_success,
                final_role=final_role,
            )
        )

    primary_chain_success = any(c.success for c in chains)
    escalated = False
    emergency_attempts: list[NotifyChannelResult] = []

    # 自动升级：主链全部失败 且 存在紧急通道 → 逐个尝试紧急通道
    if not primary_chain_success and emergency_channels:
        escalated = True
        for em_ch in emergency_channels:
            if em_ch.id in tried:
                continue
            em_result = _attempt(
                em_ch, payload, "emergency", None, db, request_id, tried
            )
            emergency_attempts.append(em_result)
            flat_results.append(em_result)

    overall_success = primary_chain_success or any(
        r.success for r in emergency_attempts
    )

    db.commit()

    return NotifyResponse(
        success=overall_success,
        request_id=request_id,
        chains=chains,
        emergency_attempts=emergency_attempts,
        escalated=escalated,
        results=flat_results,
    )


def dispatch_single(channel: Channel, db: Session) -> NotifyChannelResult:
    """单通道测试发送，不走备用/紧急链路；用于 /admin/api/channels/{id}/test。"""
    request_id = str(uuid.uuid4())
    try:
        config = registry.validate(channel.type, dict(channel.config))
        sender = registry.get(channel.type)
        success, detail = sender.send(
            title="push-aio 测试通知",
            content="这是一条测试消息，用于确认渠道配置可用。",
            config=config,
            target=channel.default_target,
        )
    except Exception as exc:
        success, detail = False, str(exc)

    db.add(
        DeliveryLog(
            request_id=request_id,
            channel_id=channel.id,
            channel_name=channel.name,
            channel_type=channel.type,
            role="primary",
            original_channel_id=None,
            success=success,
            target=channel.default_target,
            title="push-aio 测试通知",
            detail=detail,
        )
    )
    db.commit()
    return NotifyChannelResult(
        channel_id=channel.id,
        channel_name=channel.name,
        channel_type=channel.type,
        success=success,
        target=channel.default_target,
        detail=detail,
        role="primary",
        original_channel_id=None,
    )
