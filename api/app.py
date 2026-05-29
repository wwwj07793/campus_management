from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, ENVIRONMENT, INIT_DB_ON_STARTUP
from api.routers.analytics import router as analytics_router
from api.routers.auth import router as auth_router
from api.routers.courses import router as courses_router
from api.routers.enrollments import router as enrollments_router
from api.routers.grades import router as grades_router
from api.routers.students import router as students_router
from data.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    if INIT_DB_ON_STARTUP:
        init_db()
    yield


def configure_api(app: FastAPI) -> FastAPI:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["system"])
    def health_check():
        return {
            "status": "ok",
            "environment": ENVIRONMENT,
            "time": datetime.now(timezone.utc).isoformat(),
        }

    app.include_router(auth_router)
    app.include_router(students_router)
    app.include_router(courses_router)
    app.include_router(enrollments_router)
    app.include_router(grades_router)
    app.include_router(analytics_router)
    return app


def create_app() -> FastAPI:
    app = FastAPI(title="校园数据管理系统", version="0.1.0", lifespan=lifespan)
    return configure_api(app)


app = create_app()
