from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
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
from .format_adapter import convert_content, resolve_format


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

    格式适配：
    - 通过兼容层 resolve_format 决策最终格式（渠道支持就用请求格式，否则降级）
    - 通过兼容层 convert_content 转换 content 到最终格式
    - 传 content_format 给渠道 send 方法，渠道按此构造 payload
    """
    sender = registry.get(channel.type)
    target = channel.default_target
    config = dict(channel.config)
    # email 的附件仍通过 config 传递（格式信息通过 content_format 参数传递）
    if channel.type == "email":
        config["_attachments"] = [
            attachment.model_dump() for attachment in (payload.attachments or [])
        ]

    # 兼容层：决策最终格式 + 转换 content
    requested_format = payload.content_type  # plain/markdown/html
    final_format = resolve_format(
        requested_format, sender.supported_formats, sender.preferred_format
    )
    converted_content = convert_content(payload.content, requested_format, final_format)

    last_result: SendResult | None = None
    for attempt in range(2):  # 首次 + 1 次瞬时重试
        try:
            config_validated = registry.validate(channel.type, config)
            return sender.send(
                title=payload.title,
                content=converted_content,
                content_format=final_format,
                config=config_validated,
                target=target,
                extra=payload.extra,
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
    """按渠道类型分组的调度：同类型主备用渠道按顺序逐个尝试 → 全失败升级全局紧急层级（并发发送）。

    外部调用方（NotifyRequest）必须传 channel_type 指定渠道类型（如 "dingtalk_bot"）：
    - 在该类型的启用非紧急渠道里按 priority 逐个尝试（主推送 → 备用1 → 备用2 ...） → 全失败升级全局紧急层级

    WebUI 测试发送（AdminNotifyRequest）可选传 channel_ids 限定测试具体渠道。

    紧急层级并发策略（与主备用的逐个尝试不同）：
    - 所有启用的紧急渠道**同时并发发送**，不提前停止，确保最大送达率
    - 发送（纯 I/O）用 ThreadPoolExecutor 并发；日志写入在主线程串行执行避免 session 线程安全问题
    - success = 任一紧急渠道成功即整体成功

    切换决策（基于 error_kind）：
    - 主备用渠道：任何失败都触发切换到下一个渠道
    - 限流(rate_limit) 是最典型的切换场景：当前渠道被限流，立即切下一个
    - 同类型主备用全部失败时，升级到全局紧急层级并发发送
    """
    request_id = str(uuid.uuid4())

    # 同类型主备用渠道：启用的非紧急通道（按 priority 升序）
    primary_query = select(Channel).where(
        Channel.enabled.is_(True),
        Channel.is_emergency.is_(False),
    )
    # 外部调用必须指定渠道类型；WebUI 测试可指定具体渠道 ID
    channel_type = getattr(payload, "channel_type", None)
    channel_ids = getattr(payload, "channel_ids", None)
    if channel_type:
        primary_query = primary_query.where(Channel.type == channel_type)
    if channel_ids:
        primary_query = primary_query.where(Channel.id.in_(channel_ids))
    main_channels = list(
        db.scalars(primary_query.order_by(Channel.priority.asc(), Channel.id.asc())).all()
    )

    # 全局紧急层级：全局兜底，不按 channel_type 筛选（共用）
    # 仅在同类型主备用全失败时自动升级。WebUI 测试 channel_ids 时也限定范围。
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

    # 同类型主备用渠道：按顺序逐个尝试，任一成功即停止
    main_attempts: list[NotifyChannelResult] = []
    for channel in main_channels:
        result = _attempt(channel, payload, "primary", db, request_id)
        main_attempts.append(result)
        flat_results.append(result)
        if result.success:
            break

    # 同类型主备用全失败 且 存在紧急通道 → 升级到全局紧急层级并发发送（全部都发，不提前停止）
    escalated = False
    emergency_attempts: list[NotifyChannelResult] = []
    main_success = any(r.success for r in main_attempts)
    if not main_success and emergency_channels:
        escalated = True
        # 紧急渠道并发发送：发送（纯 I/O）用线程池，日志写入主线程串行
        # 这样既实现并发提速，又避免 SQLAlchemy session 的线程安全问题
        max_workers = min(len(emergency_channels), 8)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # executor.map 保证返回顺序与 emergency_channels 一致
            send_results = list(
                executor.map(lambda ch: _send_one(ch, payload), emergency_channels)
            )
        # 主线程串行写日志 + 构造结果
        for channel, result in zip(emergency_channels, send_results):
            db.add(
                DeliveryLog(
                    request_id=request_id,
                    channel_id=channel.id,
                    channel_name=channel.name,
                    channel_type=channel.type,
                    role="emergency",
                    original_channel_id=None,
                    success=result.success,
                    target=channel.default_target,
                    title=payload.title,
                    detail=result.detail,
                    error_kind=result.error_kind if not result.success else "none",
                )
            )
            attempt_result = NotifyChannelResult(
                channel_id=channel.id,
                channel_name=channel.name,
                channel_type=channel.type,
                success=result.success,
                target=channel.default_target,
                detail=result.detail,
                role="emergency",
                original_channel_id=None,
                error_kind=result.error_kind if not result.success else "none",
            )
            emergency_attempts.append(attempt_result)
            flat_results.append(attempt_result)

    overall_success = main_success or any(r.success for r in emergency_attempts)

    # ===== 计算总结字段：最终成功通道 + 角色（主/备用/紧急）+ 总尝试次数 =====
    final_channel_id: int | None = None
    final_channel_name: str | None = None
    final_channel_type: str | None = None
    final_role: str | None = None

    if overall_success:
        if main_success:
            # 同类型层级命中：第一个成功的就是最终渠道
            # 角色判定：如果它是 main_attempts[0] → primary；否则 → backup（前面有失败）
            success_idx = next(i for i, r in enumerate(main_attempts) if r.success)
            final = main_attempts[success_idx]
            final_channel_id = final.channel_id
            final_channel_name = final.channel_name
            final_channel_type = final.channel_type
            final_role = "primary" if success_idx == 0 else "backup"
        else:
            # 全局紧急层级命中：取第一个成功的（紧急层级是并发发送，按 priority 顺序取第一个成功者）
            success_idx = next(i for i, r in enumerate(emergency_attempts) if r.success)
            final = emergency_attempts[success_idx]
            final_channel_id = final.channel_id
            final_channel_name = final.channel_name
            final_channel_type = final.channel_type
            final_role = "emergency"

    db.commit()

    return NotifyResponse(
        success=overall_success,
        request_id=request_id,
        main_attempts=main_attempts,
        emergency_attempts=emergency_attempts,
        escalated=escalated,
        results=flat_results,
        final_channel_id=final_channel_id,
        final_channel_name=final_channel_name,
        final_channel_type=final_channel_type,
        final_role=final_role,
        total_attempts=len(flat_results),
    )


def dispatch_single(channel: Channel, db: Session) -> NotifyChannelResult:
    """单通道测试发送，不走主/紧急链路；用于 /admin/api/channels/{id}/test。"""
    request_id = str(uuid.uuid4())
    try:
        config = registry.validate(channel.type, dict(channel.config))
        sender = registry.get(channel.type)
        # 测试发送用 plain 格式（最通用，所有渠道都支持）
        result = sender.send(
            title="PushHub 测试通知",
            content="这是一条测试消息，用于确认渠道配置可用。",
            content_format="plain",
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
            title="PushHub 测试通知",
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


def probe_channel(payload: ChannelCreate) -> NotifyChannelResult:
    """保存前试发：不写入数据库、不写日志，仅用表单配置直接发一条测试消息。

    用于 WebUI「保存渠道」前的预检：配置可用再保存，避免存入无效渠道。
    返回 NotifyChannelResult，channel_id/channel_name 用临时占位（未持久化）。
    """
    try:
        config = registry.validate(payload.type, dict(payload.config))
        sender = registry.get(payload.type)
        # 测试发送用 plain 格式（最通用，所有渠道都支持）
        result = sender.send(
            title="PushHub 测试通知",
            content="这是一条测试消息，用于确认渠道配置可用。",
            content_format="plain",
            config=config,
            target=payload.default_target,
        )
    except ValueError as exc:
        result = SendResult.fail(f"配置错误: {exc}", "config")
    except Exception as exc:
        result = SendResult.fail(str(exc), "channel_error")

    return NotifyChannelResult(
        channel_id=0,
        channel_name=payload.name,
        channel_type=payload.type,
        success=result.success,
        target=payload.default_target,
        detail=result.detail,
        role="primary",
        original_channel_id=None,
        error_kind=result.error_kind if not result.success else "none",
    )
