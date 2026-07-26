from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select

from .db import session_scope
from ..models import Setting


# API Key 在 DB 中的键名
_API_KEY_SETTING_KEY = "api_key"

# 内存缓存：避免每次请求都查 DB
_API_KEY: Optional[str] = None
# 是否已从 DB 加载过（用于区分"首次启动未设置"和"加载失败"）
_LOADED: bool = False

# 始终公开的管理接口路径（不需要 API Key）
# - /admin/api/auth/status: 让前端检测当前是否需要首次设置
# - /admin/api/auth/setup:  首次设置 API Key（仅在 setup 模式下放行）
_PUBLIC_PATHS = {"/admin/api/auth/status"}


def _load_api_key_from_db() -> None:
    """从 DB 加载 API Key 到内存缓存。启动时调用一次。"""
    global _API_KEY, _LOADED
    with session_scope() as db:
        row = db.scalar(select(Setting).where(Setting.key == _API_KEY_SETTING_KEY))
        _API_KEY = row.value if row else None
    _LOADED = True


def is_setup_mode() -> bool:
    """是否处于首次设置模式（DB 中尚未配置 API Key）。

    True 表示首次启动，前端应跳转到 setup 页面让用户设置密钥。
    """
    if not _LOADED:
        _load_api_key_from_db()
    return not _API_KEY


def get_api_key() -> str:
    """返回当前生效的 API Key（setup 模式下返回空串）。"""
    if not _LOADED:
        _load_api_key_from_db()
    return _API_KEY or ""


def set_api_key(new_key: str) -> None:
    """写入 API Key 到 DB（首次设置 + 修改都走这个），立即生效。

    修改后无需重启服务。
    """
    global _API_KEY
    if not new_key:
        raise HTTPException(status_code=400, detail="新 Key 不能为空")
    if len(new_key) < 12:
        raise HTTPException(status_code=400, detail="新 Key 至少 12 位，保证强度")

    with session_scope() as db:
        row = db.scalar(select(Setting).where(Setting.key == _API_KEY_SETTING_KEY))
        if row:
            row.value = new_key
        else:
            db.add(Setting(key=_API_KEY_SETTING_KEY, value=new_key))

    # 同步更新内存缓存
    _API_KEY = new_key


def verify_api_key(request: Request) -> None:
    """FastAPI 依赖：校验请求头 X-API-Key。

    - 始终放行 /admin/api/auth/status（让前端检测状态）
    - setup 模式下放行 /admin/api/auth/setup（首次设置），其他接口返回 401 提示先初始化
    - 正常模式下校验 X-API-Key
    """
    path = request.url.path

    # 始终公开的状态查询接口
    if path in _PUBLIC_PATHS:
        return

    # 首次设置模式
    if is_setup_mode():
        if path == "/admin/api/auth/setup":
            return  # 放行首次设置接口
        raise HTTPException(
            status_code=401,
            detail="首次启动尚未设置 API Key，请先访问 WebUI 完成初始化设置。",
        )

    # 正常鉴权
    provided = request.headers.get("X-API-Key", "")
    if not provided or not secrets.compare_digest(provided, _API_KEY or ""):
        raise HTTPException(
            status_code=401,
            detail="无效或缺失的 API Key。请在请求头携带 X-API-Key。",
        )


# 所有需要鉴权的接口共享这个依赖
RequireApiKey = Depends(verify_api_key)
