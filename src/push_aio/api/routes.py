from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.db import get_db
from ..models import Channel, DeliveryLog
from ..schemas import (
    BackupGroupUpdate,
    ChannelCreate,
    ChannelMeta,
    ChannelOut,
    ChannelStatusOut,
    ChannelUpdate,
    DeliveryLogOut,
    NotifyChannelResult,
    NotifyRequest,
    NotifyResponse,
    PlatformStatusOut,
)
from ..services.channels import registry
from ..services.dispatcher import dispatch, dispatch_single

router = APIRouter(prefix="/api")


def _serialize_channel(channel: Channel) -> ChannelOut:
    return ChannelOut.model_validate(channel)


def _channel_status(channel: Channel) -> ChannelStatusOut:
    try:
        sender = registry.get(channel.type)
        registry.validate(channel.type, channel.config)
        configured = True
        online = channel.enabled
        detail = "已启用，配置有效" if channel.enabled else "配置有效，但渠道已禁用"
        label = sender.label
        target_mode = sender.target_mode
    except Exception as exc:
        configured = False
        online = False
        detail = f"配置无效: {exc}"
        label = channel.type
        target_mode = "embedded"

    return ChannelStatusOut(
        id=channel.id,
        name=channel.name,
        type=channel.type,
        label=label,
        enabled=channel.enabled,
        configured=configured,
        online=online,
        target_mode=target_mode,
        default_target=channel.default_target,
        is_emergency=channel.is_emergency,
        priority=channel.priority,
        backup_channel_ids=list(channel.backup_channel_ids or []),
        detail=detail,
    )


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/channel-types", response_model=list[ChannelMeta])
def channel_types():
    return registry.meta()


@router.get("/channels/status", response_model=list[ChannelStatusOut])
def channel_statuses(db: Session = Depends(get_db)):
    channels = db.scalars(select(Channel).order_by(Channel.id.asc())).all()
    return [_channel_status(channel) for channel in channels]


@router.get("/status", response_model=PlatformStatusOut)
def platform_status(db: Session = Depends(get_db)):
    channels = db.scalars(select(Channel).order_by(Channel.id.asc())).all()
    statuses = [_channel_status(channel) for channel in channels]
    return PlatformStatusOut(
        ok=True,
        supported_count=len(registry.meta()),
        configured_count=len(statuses),
        enabled_count=sum(1 for item in statuses if item.enabled),
        online_count=sum(1 for item in statuses if item.online),
        emergency_count=sum(1 for item in statuses if item.is_emergency and item.enabled),
        supported_types=registry.meta(),
        channels=statuses,
    )


@router.get("/channels", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db)):
    channels = db.scalars(select(Channel).order_by(Channel.id.desc())).all()
    return [_serialize_channel(item) for item in channels]


@router.post("/channels", response_model=ChannelOut)
def create_channel(payload: ChannelCreate, db: Session = Depends(get_db)):
    validated_config = registry.validate(payload.type, payload.config)
    channel = Channel(
        name=payload.name,
        type=payload.type,
        enabled=payload.enabled,
        default_target=payload.default_target,
        config=validated_config,
        backup_channel_ids=payload.backup_channel_ids,
        is_emergency=payload.is_emergency,
        priority=payload.priority,
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return _serialize_channel(channel)


@router.put("/channels/{channel_id}", response_model=ChannelOut)
def update_channel(channel_id: int, payload: ChannelUpdate, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    if payload.name is not None:
        channel.name = payload.name
    if payload.enabled is not None:
        channel.enabled = payload.enabled
    if payload.default_target is not None:
        channel.default_target = payload.default_target
    if payload.config is not None:
        channel.config = registry.validate(channel.type, payload.config)
    if payload.backup_channel_ids is not None:
        # 不允许把本通道自己设为备用
        channel.backup_channel_ids = [
            cid for cid in payload.backup_channel_ids if cid != channel.id
        ]
    if payload.is_emergency is not None:
        channel.is_emergency = payload.is_emergency
    if payload.priority is not None:
        channel.priority = payload.priority

    db.add(channel)
    db.commit()
    db.refresh(channel)
    return _serialize_channel(channel)


@router.put("/channels/{channel_id}/backups", response_model=ChannelOut)
def update_backup_group(
    channel_id: int, payload: BackupGroupUpdate, db: Session = Depends(get_db)
):
    """单独更新某渠道的备用组。"""
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    channel.backup_channel_ids = [cid for cid in payload.backup_channel_ids if cid != channel.id]
    db.add(channel)
    db.commit()
    db.refresh(channel)
    return _serialize_channel(channel)


@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    db.delete(channel)
    db.commit()
    return {"success": True}


@router.post("/channels/{channel_id}/test", response_model=NotifyChannelResult)
def test_channel(channel_id: int, db: Session = Depends(get_db)):
    channel = db.get(Channel, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")
    return dispatch_single(channel, db)


@router.get("/channels/emergency", response_model=list[ChannelOut])
def list_emergency_channels(db: Session = Depends(get_db)):
    """查询所有紧急通道，便于前端独立展示。"""
    channels = db.scalars(
        select(Channel)
        .where(Channel.is_emergency.is_(True))
        .order_by(Channel.priority.asc(), Channel.id.asc())
    ).all()
    return [_serialize_channel(item) for item in channels]


@router.post("/notify", response_model=NotifyResponse)
def notify(payload: NotifyRequest, db: Session = Depends(get_db)):
    # 主通道筛选：若指定了 ids/types/names 但完全没匹配到，且无紧急通道兜底，则 404
    if payload.channel_ids or payload.channel_types or payload.channel_names:
        query = select(Channel.id).where(Channel.enabled.is_(True))
        if payload.channel_ids:
            query = query.where(Channel.id.in_(payload.channel_ids))
        if payload.channel_types:
            query = query.where(Channel.type.in_(payload.channel_types))
        if payload.channel_names:
            query = query.where(Channel.name.in_(payload.channel_names))
        has_primary = db.scalar(query.limit(1)) is not None
        has_emergency = db.scalar(
            select(Channel.id)
            .where(Channel.enabled.is_(True), Channel.is_emergency.is_(True))
            .limit(1)
        ) is not None
        if not has_primary and not has_emergency:
            raise HTTPException(status_code=404, detail="未找到可用渠道，且无紧急通道兜底")
    return dispatch(payload, db)


@router.get("/logs", response_model=list[DeliveryLogOut])
def list_logs(db: Session = Depends(get_db)):
    logs = db.scalars(select(DeliveryLog).order_by(DeliveryLog.id.desc()).limit(50)).all()
    return [DeliveryLogOut.model_validate(item) for item in logs]


@router.get("/logs/{request_id}", response_model=list[DeliveryLogOut])
def list_logs_by_request(request_id: str, db: Session = Depends(get_db)):
    """按一次 notify 调用聚合所有尝试日志，便于复盘链路。"""
    logs = db.scalars(
        select(DeliveryLog)
        .where(DeliveryLog.request_id == request_id)
        .order_by(DeliveryLog.id.asc())
    ).all()
    return [DeliveryLogOut.model_validate(item) for item in logs]
