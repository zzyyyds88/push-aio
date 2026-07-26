from __future__ import annotations

import uuid
from typing import Any

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Channel, DeliveryLog
from ..schemas import (
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
    payload: NotifyRequest,
    target_override: str | None,
    config_override: dict[str, Any] | None,
) -> tuple[bool, str, str | None]:
    """对单通道执行 1+1 重试发送，返回 (success, detail, target)。"""
    sender = registry.get(channel.type)
    target = target_override or channel.default_target
    config = dict(channel.config)
    if config_override:
        config.update(config_override)
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
    payload: NotifyRequest,
    role: str,
    original_channel_id: int | None,
    db: Session,
    request_id: str,
    tried: dict[int, NotifyChannelResult],
) -> NotifyChannelResult:
    """对一个通道做一次完整尝试；同请求内已尝试的通道直接复用结果不重发。"""
    if channel.id in tried:
        cached = tried[channel.id]
        # 复用已有结果，但替换角色与原始主通道，便于链路展示
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

    target_override = (payload.target_overrides or {}).get(channel.id)
    config_override = (payload.config_overrides or {}).get(channel.id)
    success, detail, target = _send_one(channel, payload, target_override, config_override)

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


def dispatch(payload: NotifyRequest, db: Session) -> NotifyResponse:
    """主→备→紧急 调度。"""
    request_id = str(uuid.uuid4())

    query = select(Channel).where(Channel.enabled.is_(True))
    if payload.channel_ids:
        query = query.where(Channel.id.in_(payload.channel_ids))
    if payload.channel_types:
        query = query.where(Channel.type.in_(payload.channel_types))
    if payload.channel_names:
        query = query.where(Channel.name.in_(payload.channel_names))
    primary_channels = list(
        db.scalars(query.order_by(Channel.priority.asc(), Channel.id.asc())).all()
    )

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
    emergency_attempts: list[NotifyChannelResult] = []

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

    # 紧急触发：显式标记 与 主链全失败升级
    if payload.priority == "emergency" or payload.force_emergency:
        for em_ch in emergency_channels:
            if em_ch.id in tried:
                # 紧急通道复用主链结果时，也作为 emergency 角色记一条
                cached = tried[em_ch.id]
                emergency_attempts.append(
                    NotifyChannelResult(
                        channel_id=cached.channel_id,
                        channel_name=cached.channel_name,
                        channel_type=cached.channel_type,
                        success=cached.success,
                        target=cached.target,
                        detail=f"复用本次请求已尝试结果：{cached.detail}",
                        role="emergency",
                        original_channel_id=None,
                    )
                )
                continue
            em_result = _attempt(
                em_ch, payload, "emergency", None, db, request_id, tried
            )
            emergency_attempts.append(em_result)
            flat_results.append(em_result)
    elif not primary_chain_success and emergency_channels:
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
        priority=payload.priority,
        chains=chains,
        emergency_attempts=emergency_attempts,
        escalated=escalated,
        results=flat_results,
    )


def dispatch_single(channel: Channel, db: Session) -> NotifyChannelResult:
    """单通道测试发送，不走备用/紧急链路；用于 /api/channels/{id}/test。"""
    sender = registry.get(channel.type)
    target = channel.default_target
    request_id = str(uuid.uuid4())
    try:
        config = registry.validate(channel.type, dict(channel.config))
        success, detail = sender.send(
            title="push-aio 测试通知",
            content="这是一条测试消息，用于确认渠道配置可用。",
            config=config,
            target=target,
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
            target=target,
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
        target=target,
        detail=detail,
        role="primary",
        original_channel_id=None,
    )
