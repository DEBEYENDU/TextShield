"""TextShield - FastAPI application entry point.

Serves the REST API (``/api/*``) and the web dashboard (templates +
static assets) with a clean layout:
    API -> routers  (analysis, history, stats, health)
    ORM -> app/database, app/services
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import __version__
from app.api import routes_analysis, routes_health, routes_history, routes_stats
from app.core.config import BASE_DIR, settings
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_TITLE,
    version=__version__,
    description=settings.APP_TAGLINE,
)

# ------------------------------------------------------------ static assets
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "app" / "templates"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# ------------------------------------------------------------ routers
app.include_router(routes_analysis.router)
app.include_router(routes_history.router)
app.include_router(routes_stats.router)
app.include_router(routes_health.router)


def _render(request: Request, template: str):
    return templates.TemplateResponse(
        request=request,
        name=template,
        context={"title": settings.APP_TITLE, "tagline": settings.APP_TAGLINE},
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return _render(request, "index.html")


@app.get("/history", response_class=HTMLResponse)
def history_page(request: Request):
    return _render(request, "history.html")


@app.get("/analytics", response_class=HTMLResponse)
def analytics_page(request: Request):
    return _render(request, "analytics.html")


@app.get("/knowledge-base", response_class=HTMLResponse)
def knowledge_base_page(request: Request):
    return _render(request, "knowledge_base.html")


@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return _render(request, "about.html")