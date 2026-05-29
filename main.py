from __future__ import annotations

import mimetypes
import os

from fastapi import FastAPI
from starlette.responses import FileResponse

from api.app import configure_api, lifespan

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend-demo")


def create_app() -> FastAPI:
    app = FastAPI(title="校园数据管理系统", version="0.1.0", lifespan=lifespan)

    # API 路由先注册，精确匹配优先于兜底路由
    configure_api(app)

    # 兜底：未匹配 API 的路径 → 前端静态文件
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIR, full_path) if full_path else os.path.join(FRONTEND_DIR, "index.html")
        if os.path.isfile(file_path):
            media_type, _ = mimetypes.guess_type(file_path)
            return FileResponse(file_path, media_type=media_type or "application/octet-stream")
        # SPA fallback: return index.html for unrecognized paths
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
