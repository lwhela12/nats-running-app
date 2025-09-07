from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import auth as auth_router
from .routers import capability as capability_router
from .routers import goals as goals_router
from .routers import plans as plans_router
from .routers import workouts as workouts_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Nat's Running App API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    app.include_router(auth_router.router)
    app.include_router(capability_router.router)
    app.include_router(goals_router.router)
    app.include_router(plans_router.router)
    app.include_router(workouts_router.router)
    return app


app = create_app()
