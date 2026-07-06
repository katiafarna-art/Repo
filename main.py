from starlette.responses import HTMLResponse
import asyncio
import logging
import os
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from api.exceptionhandlers import register_exception_handlers
from api.routers import register_routers
from bdlpkg.utils.bdlfile.services.bdlfile import get_obj_from_config_path
from bdlpkg.utils.worker.services.job import JobManager
from core.routines.services.pid_registry import scan_stale, unregister as pid_unregister

_REAPER_INTERVAL = int(os.getenv("JM_REAPER_INTERVAL", "60"))


async def _job_reaper_loop():
    """Background task: reaps dead local jobs and removes orphan PID files."""
    while True:
        await asyncio.sleep(_REAPER_INTERVAL)
        jm = JobManager()
        removed = []
        for name in list(jm._jobs):
            proc = jm._jobs[name].get("job_process")
            if proc is not None and not proc.is_alive():
                proc.join(timeout=1)
                jm._jobs.pop(name, None)
                removed.append(name)
        if removed:
            logging.info(f"[jm-reaper] reaped {len(removed)} local zombie(s): {removed}")
        for job_id in scan_stale():
            pid_unregister(job_id)
            logging.info(f"[jm-reaper] cleaned stale PID file for orphan: {job_id}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: starts the reaper on startup, cancels it and joins local zombies on shutdown."""
    task = asyncio.create_task(_job_reaper_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        jm = JobManager()
        for name in list(jm._jobs):
            proc = jm._jobs[name].get("job_process")
            if proc is not None and not proc.is_alive():
                proc.join(timeout=1)
                jm._jobs.pop(name, None)


app_configs = get_obj_from_config_path("app.yaml")
if "ISP_AMBIENTE" in os.environ:
    STATIC_DIRECTORY = os.path.join(
        os.getenv("VIRTUAL_ENV", "/opt/app-root"), "com.intesasanpaolo.bdl", "static"
    )
else:
    STATIC_DIRECTORY = "static"

if 'ISP_AMBIENTE' in os.environ:
    from . import __package_name__, __version__

    packet_name = __package_name__
    versione = __version__
    title = packet_name
else:
    versione = f"dev {os.getenv('USER',os.getenv('USERNAME','localuser'))}@{os.getenv('HOSTNAME',os.getenv('COMPUTERNAME','localuser'))}"
    title = app_configs["application"]["name"]

tags_metadata = app_configs["tags_metadata"]
tags_metadata.insert(
    0,
    {
        "name": app_configs["application"]["name"],
        "description": app_configs["short_description"],
    },
)

app = FastAPI(
    lifespan=lifespan,
    title=title,
    description=app_configs["description"],
    openapi_tags=tags_metadata,
    version=versione,
    docs_url=None,
    redoc_url=None,
)

# https://fastapi.tiangolo.com/advanced/extending-openapi/#self-hosting-javascript-and-css-for-docs

try:
    app.mount("/static", StaticFiles(directory=STATIC_DIRECTORY), name="static")
except:
    logging.warning("No static path")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html() -> HTMLResponse:
    return get_swagger_ui_html(
        openapi_url="./openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="./static/swagger-ui-bundle.js",
        swagger_css_url="./static/swagger-ui.css",
        swagger_favicon_url="./static/LogoBdL.jpg",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
    return get_swagger_ui_oauth2_redirect_html()


register_exception_handlers(app)
register_routers(app)
