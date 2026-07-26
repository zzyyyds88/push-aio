from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request


# 项目根目录：src/push_aio/core/security.py → parents[3]
BASE_DIR = Path(__file__).resolve().parents[3]

# 启动时加载 .env（已 gitignore，不入仓库）
load_dotenv(BASE_DIR / ".env")

# 全局单一 API Key（个人推送中心，无需多 Key）
# 优先读环境变量 PUSH_AIO_API_KEY；未设置则启动失败，避免裸奔。
_API_KEY: str | None = os.environ.get("PUSH_AIO_API_KEY")


def get_api_key() -> str:
    """返回当前生效的 API Key。"""
    return _API_KEY or ""


def ensure_api_key_configured() -> None:
    """启动时调用：未配置 API Key 则拒绝启动（公网部署不允许裸奔）。"""
    if not _API_KEY or _API_KEY == "change-me-to-a-random-string":
        print(
            "\n[安全] 未配置 API Key。请：\n"
            "  1. 复制 .env.example 为 .env：cp .env.example .env\n"
            "  2. 填入随机 Key（PowerShell 生成 32 位随机串）：\n"
            '     -join ((48..57)+(65..90)+(97..122) | Get-Random -Count 32 | % {[char]$_})\n'
            "  3. 重启服务\n",
            file=sys.stderr,
        )
        sys.exit(1)


def verify_api_key(request: Request) -> None:
    """FastAPI 依赖：校验请求头 X-API-Key。未通过返回 401。"""
    provided = request.headers.get("X-API-Key", "")
    # 使用 secrets.compare_digest 防止时序攻击
    if not provided or not secrets.compare_digest(provided, _API_KEY or ""):
        raise HTTPException(
            status_code=401,
            detail="无效或缺失的 API Key。请在请求头携带 X-API-Key。",
        )


# 所有需要鉴权的接口共享这个依赖
RequireApiKey = Depends(verify_api_key)
