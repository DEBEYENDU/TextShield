"""TextShield - FastAPI application entry point.

Composition root: builds the app via ``create_app`` (a factory) so
tests and tooling get a clean instance per run:

    API -> routers (analysis, history, stats, system, knowledge-base)
    Services -> app/services (orchestration, no business logic in routes)
    Data -> app/database (migrations + repositories)
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.api import (
    routes_analysis,
    routes_history,
    routes_knowledge,
    routes_stats,
    routes_system,
)
from app.api.middleware import LoggingMiddleware, RequestIDMiddleware
from app.core.container import ServiceRegistry, create_container, verify_container
from app.core.errors import register_exception_handlers
from app.core.logging import get_logger, setup_logging
from app.core.settings import settings
from app.database.base import init_db
from app.services.system_status_service import mark_started

setup_logging()
logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "app" / "templates"


def _render(request: Request, templates: Jinja2Templates, template: str):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={"title": settings.APP_TITLE, "tagline": settings.APP_TAGLINE},
    )


def _register_page_routes(app: FastAPI, templates: Jinja2Templates) -> None:
    pages = [
        ("/", "index.html"),
        ("/history", "history.html"),
        ("/analytics", "analytics.html"),
        ("/knowledge-base", "knowledge_base.html"),
        ("/about", "about.html"),
        ("/dashboard", "dashboard.html"),
        ("/analyze", "analyze.html"),
        ("/results", "results.html"),
        ("/evidence", "evidence.html"),
        ("/knowledge", "knowledge.html"),
        ("/system", "system.html"),
        ("/settings", "settings.html"),
    ]

    def _page_handler(template: str):
        def handler(request: Request) -> HTMLResponse:
            return _render(request, templates, template)

        return handler

    for path, template in pages:
        app.add_api_route(
            path,
            _page_handler(template),
            response_class=HTMLResponse,
            include_in_schema=False,
        )


def _register_api_routes(app: FastAPI) -> None:
    for router_module in (
        routes_analysis,
        routes_history,
        routes_stats,
        routes_system,
        routes_knowledge,
    ):
        app.include_router(router_module.router)


def create_app(registry: ServiceRegistry | None = None) -> FastAPI:
    """Application factory. Builds a fresh app with its own service registry."""
    container = create_container(registry or ServiceRegistry())
    missing = verify_container(container, logger)
    if missing:
        raise RuntimeError(f"Container missing required services: {missing}")

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        init_db()
        mark_started()
        logger.info(
            "TextShield v%s starting (env=%s, db=%s)",
            __version__,
            settings.ENVIRONMENT,
            settings.database_path,
        )
        yield
        logger.info("TextShield shutting down")

    app = FastAPI(
        title=settings.APP_TITLE,
        version=__version__,
        description=settings.APP_TAGLINE,
        lifespan=lifespan,
    )
    app.state.registry = container
    app.state.start_time_iso = None

    register_exception_handlers(app)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    templates = Jinja2Templates(directory=str(TEMPLATE_DIR))
    _register_api_routes(app)
    _register_page_routes(app, templates)
    return app


app = create_app()
