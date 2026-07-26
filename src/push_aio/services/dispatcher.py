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
    - 限流/认证/配置/业务错误 → 不重试，直接返回（让调度器切下一个通道）
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
    db: Session,
    request_id: str,
) -> NotifyChannelResult:
    """对一个通道做一次完整尝试并记录日志。"""
    result = _send_one(channel, payload)

    db.add(
        DeliveryLog(
            request_id=request_id,
            channel_id=channel.id,
            channel_name=channel.name,
            channel_type=channel.type,
            role=role,
            original_channel_id=None,
            success=result.success,
            target=channel.default_target,
            title=payload.title,
            detail=result.detail,
            error_kind=result.error_kind if not result.success else "none",
        )
    )

    return NotifyChannelResult(
        channel_id=channel.id,
        channel_name=channel.name,
        channel_type=channel.type,
        success=result.success,
        target=channel.default_target,
        detail=result.detail,
        role=role,
        original_channel_id=None,
        error_kind=result.error_kind if not result.success else "none",
    )


def dispatch(
    payload: NotifyRequest | AdminNotifyRequest,
    db: Session,
) -> NotifyResponse:
    """全局有序列表调度：主通道组按顺序逐个尝试 → 全失败升级紧急通道组。

    外部调用方（NotifyRequest）和 WebUI 测试发送（AdminNotifyRequest）共用此函数。
    AdminNotifyRequest 可选传 channel_ids 限定测试范围，不传则对所有启用通道走完整调度。

    切换决策（基于 error_kind）：
    - 任何失败（rate_limit/auth/config/network/channel_error）都触发切换到下一个通道
    - 限流(rate_limit) 是最典型的切换场景：当前通道被限流，立即切下一个
    - 主通道组全部失败时，升级到紧急通道组
    """
    request_id = str(uuid.uuid4())

    # 主通道组：所有启用的非紧急通道（按 priority 升序）
    primary_query = select(Channel).where(
        Channel.enabled.is_(True),
        Channel.is_emergency.is_(False),
    )
    # AdminNotifyRequest 可限定测试渠道
    channel_ids = getattr(payload, "channel_ids", None)
    if channel_ids:
        primary_query = primary_query.where(Channel.id.in_(channel_ids))
    main_channels = list(
        db.scalars(primary_query.order_by(Channel.priority.asc(), Channel.id.asc())).all()
    )

    # 紧急通道组：仅在主通道组全失败时自动升级
    emergency_query = select(Channel).where(
        Channel.enabled.is_(True),
        Channel.is_emergency.is_(True),
    )
    if channel_ids:
        emergency_query = emergency_query.where(Channel.id.in_(channel_ids))
    emergency_channels = list(
        db.scalars(emergency_query.order_by(Channel.priority.asc(), Channel.id.asc())).all()
    )

    flat_results: list[NotifyChannelResult] = []

    # 主通道组：按顺序逐个尝试，任一成功即停止
    main_attempts: list[NotifyChannelResult] = []
    for channel in main_channels:
        result = _attempt(channel, payload, "primary", db, request_id)
        main_attempts.append(result)
        flat_results.append(result)
        if result.success:
            break

    # 主通道组全失败 且 存在紧急通道 → 升级到紧急通道组逐个尝试
    escalated = False
    emergency_attempts: list[NotifyChannelResult] = []
    main_success = any(r.success for r in main_attempts)
    if not main_success and emergency_channels:
        escalated = True
        for channel in emergency_channels:
            result = _attempt(channel, payload, "emergency", db, request_id)
            emergency_attempts.append(result)
            flat_results.append(result)
            if result.success:
                break

    overall_success = main_success or any(r.success for r in emergency_attempts)

    db.commit()

    return NotifyResponse(
        success=overall_success,
        request_id=request_id,
        main_attempts=main_attempts,
        emergency_attempts=emergency_attempts,
        escalated=escalated,
        results=flat_results,
    )


def dispatch_single(channel: Channel, db: Session) -> NotifyChannelResult:
    """单通道测试发送，不走主/紧急链路；用于 /admin/api/channels/{id}/test。"""
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
