from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import admin_router, notify_router, public_router
from .core.bootstrap import bootstrap_channels_if_needed
from .core.db import Base, engine, ensure_schema
from .core.security import ensure_api_key_configured


# 固定端口 8080：用户偏好不通过 CLI/环境变量覆盖。
APP_PORT = 8080

# 静态资源随包打包：src/push_aio/static/
STATIC_DIR = Path(__file__).resolve().parent / "static"

# 启动前强制校验：未配置 API Key 则拒绝启动（公网部署不允许裸奔）
ensure_api_key_configured()

app = FastAPI(title="push-aio", version="0.4.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自动建表（仅 create_all，不做迁移；表结构变更需手动删 data/push_aio.db 重建）
Base.metadata.create_all(bind=engine)
# 兼容旧库：对已存在的表补缺失列，避免删库丢日志
ensure_schema()
bootstrap_channels_if_needed()
app.include_router(public_router)  # /api/health（无需鉴权）
app.include_router(notify_router)  # /api/notify（外部调用，需 X-API-Key）
app.include_router(admin_router)   # /admin/api/*（WebUI 管理，需 X-API-Key）
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("push_aio.main:app", host="0.0.0.0", port=APP_PORT, reload=True)
