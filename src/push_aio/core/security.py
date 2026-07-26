from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request


# 项目根目录：src/push_aio/core/security.py → parents[3]
BASE_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = BASE_DIR / ".env"

# 启动时加载 .env（已 gitignore，不入仓库）
load_dotenv(ENV_PATH)

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


def set_api_key(new_key: str) -> None:
    """运行时修改 API Key：同步写回 .env 并更新内存中的 _API_KEY。

    修改后立即生效，无需重启服务。下次启动时由 .env 加载。
    """
    global _API_KEY
    if not new_key or new_key == "change-me-to-a-random-string":
        raise HTTPException(status_code=400, detail="新 Key 不能为空或占位符")
    if len(new_key) < 12:
        raise HTTPException(status_code=400, detail="新 Key 至少 12 位，保证强度")

    # 写回 .env：保留其他行，只替换 PUSH_AIO_API_KEY
    lines: list[str] = []
    found = False
    if ENV_PATH.exists():
        for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if raw.startswith("PUSH_AIO_API_KEY="):
                lines.append(f"PUSH_AIO_API_KEY={new_key}")
                found = True
            else:
                lines.append(raw)
    if not found:
        lines.append(f"PUSH_AIO_API_KEY={new_key}")
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 同步更新运行时
    _API_KEY = new_key
    os.environ["PUSH_AIO_API_KEY"] = new_key


# 所有需要鉴权的接口共享这个依赖
RequireApiKey = Depends(verify_api_key)
