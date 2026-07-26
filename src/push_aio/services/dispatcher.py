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
from .channels import SendResult, registry


# 视为瞬时异常：值得重试一次（仅 network 类才重试，限流/认证/配置/业务错误都不重试）
_TRANSIENT_EXCEPTIONS = (
    requests.exceptions.Timeout,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
)


def _send_one(
    channel: Channel,
    payload: NotifyRequest | AdminNotifyRequest,
) -> SendResult:
    """对单通道执行 1+1 重试发送。

    决策：
    - 网络异常（Timeout/ConnectionError）→ 重试 1 次
    - 限流/认证/配置/业务错误 → 不重试，直接返回（让调度器切换备用/紧急）
    - 成功 → 立即返回
    """
    sender = registry.get(channel.type)
    target = channel.default_target
    config = dict(channel.config)
    config["_notify_content_type"] = payload.content_type
    if channel.type == "email":
        config["_content_type"] = payload.content_type
        config["_attachments"] = [
            attachment.model_dump() for attachment in (payload.attachments or [])
        ]

    last_result: SendResult | None = None
    for attempt in range(2):  # 首次 + 1 次瞬时重试
        try:
            config_validated = registry.validate(channel.type, config)
            return sender.send(
                title=payload.title,
                content=payload.content,
                config=config_validated,
                target=target,
            )
        except _TRANSIENT_EXCEPTIONS as exc:
            # 仅网络异常才重试
            last_result = SendResult.fail(f"网络异常: {exc}", "network")
            continue
        except ValueError as exc:
            # 配置错误（缺必填/格式错）→ 不重试
            return SendResult.fail(f"配置错误: {exc}", "config")
        except Exception as exc:
            # 其他未知异常 → 视为业务错误，不重试
            return SendResult.fail(str(exc), "channel_error")
    return last_result or SendResult.fail("未知错误", "channel_error")


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
            error_kind=cached.error_kind,
        )

    result = _send_one(channel, payload)

    db.add(
        DeliveryLog(
            request_id=request_id,
            channel_id=channel.id,
            channel_name=channel.name,
            channel_type=channel.type,
            role=role,
            original_channel_id=original_channel_id,
            success=result.success,
            target=channel.default_target,
            title=payload.title,
            detail=result.detail,
            error_kind=result.error_kind if not result.success else "none",
        )
    )

    out = NotifyChannelResult(
        channel_id=channel.id,
        channel_name=channel.name,
        channel_type=channel.type,
        success=result.success,
        target=channel.default_target,
        detail=result.detail,
        role=role,
        original_channel_id=original_channel_id,
        error_kind=result.error_kind if not result.success else "none",
    )
    tried[channel.id] = out
    return out


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

    切换决策（基于 error_kind）：
    - 任何失败（rate_limit/auth/config/network/channel_error）都触发切换到备用通道
    - 限流(rate_limit) 是最典型的切换场景：当前通道被限流，立即切到备用
    - 所有主链全部失败时，升级到紧急通道
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
            # 主通道失败（含限流），按备用组顺序逐个尝试
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
    # 典型场景：主通道和备用通道都被限流/认证失败/网络异常 → 升级到紧急通道兜底
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
        result = sender.send(
            title="push-aio 测试通知",
            content="这是一条测试消息，用于确认渠道配置可用。",
            config=config,
            target=channel.default_target,
        )
    except ValueError as exc:
        result = SendResult.fail(f"配置错误: {exc}", "config")
    except Exception as exc:
        result = SendResult.fail(str(exc), "channel_error")

    db.add(
        DeliveryLog(
            request_id=request_id,
            channel_id=channel.id,
            channel_name=channel.name,
            channel_type=channel.type,
            role="primary",
            original_channel_id=None,
            success=result.success,
            target=channel.default_target,
            title="push-aio 测试通知",
            detail=result.detail,
            error_kind=result.error_kind if not result.success else "none",
        )
    )
    db.commit()
    return NotifyChannelResult(
        channel_id=channel.id,
        channel_name=channel.name,
        channel_type=channel.type,
        success=result.success,
        target=channel.default_target,
        detail=result.detail,
        role="primary",
        original_channel_id=None,
        error_kind=result.error_kind if not result.success else "none",
    )
