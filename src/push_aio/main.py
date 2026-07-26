from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .core.db import Base, engine
from .core.bootstrap import bootstrap_channels_if_needed


# 固定端口 8080：用户偏好不通过 CLI/环境变量覆盖。
APP_PORT = 8080

# 静态资源随包打包：src/push_aio/static/
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="push-aio", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 自动建表（仅 create_all，不做迁移；表结构变更需手动删 data/push_aio.db 重建）
Base.metadata.create_all(bind=engine)
bootstrap_channels_if_needed()
app.include_router(router)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("push_aio.main:app", host="0.0.0.0", port=APP_PORT, reload=True)
