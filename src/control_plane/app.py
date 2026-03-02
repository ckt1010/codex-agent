from __future__ import annotations

from fastapi import FastAPI

from common.settings import settings
from control_plane.api import agents, events, memory, sessions, tasks
from control_plane.repo.sqlite import SQLiteRepo
from control_plane.services.bootstrap import BootstrapService
from control_plane.services.dedupe import DedupeService
from control_plane.services.memory_index import MemoryIndexService
from control_plane.services.notification import NotificationFanout
from control_plane.services.oss_store import LocalOSSStore


def create_app() -> FastAPI:
    app = FastAPI(title="Codex Bridge Control Plane", version="0.1.0")

    repo = SQLiteRepo(settings.db_path)
    bootstrap = BootstrapService(repo, settings.bootstrap_ttl_seconds, settings.token_ttl_seconds)
    dedupe = DedupeService(repo)
    memory_svc = MemoryIndexService(repo)
    oss = LocalOSSStore(settings.oss_root)
    notifier = NotificationFanout(
        feishu_push_url=settings.feishu_push_url,
        imessage_push_url=settings.imessage_push_url,
        timeout_seconds=settings.connector_push_timeout_seconds,
    )

    for r in (tasks.router, agents.router, events.router, memory.router, sessions.router):
        r.repo = repo
    tasks.router.dedupe = dedupe
    agents.router.bootstrap = bootstrap
    events.router.notifier = notifier
    memory.router.memory = memory_svc
    memory.router.oss = oss
    app.state.repo = repo
    app.state.bootstrap = bootstrap
    app.state.memory = memory_svc
    app.state.oss = oss
    app.state.notifier = notifier

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.post("/api/bootstrap/new")
    def new_bootstrap_code():
        code, expires_at = bootstrap.issue_code()
        return {"bootstrap_code": code, "expires_at": expires_at}

    @app.on_event("startup")
    def on_startup() -> None:
        if settings.system_status_notify_enabled:
            notifier.notify_system_status(
                component="control-plane",
                status="started",
                detail="control-plane started successfully",
            )

    app.include_router(tasks.router)
    app.include_router(agents.router)
    app.include_router(events.router)
    app.include_router(memory.router)
    app.include_router(sessions.router)
    return app


app = create_app()
