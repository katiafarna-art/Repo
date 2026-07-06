# https://github.com/GArmane/python-fastapi-hex-todo/blob/master/todolist/api/routers/account/__init__.py
from fastapi.routing import APIRouter

from . import config, health, job, ixp

def _build_router() -> APIRouter:
    rt = APIRouter(
        tags=["Internal"]
    )
    rt.include_router(config.router, prefix="/config")
    rt.include_router(health.router, prefix="/health")
    rt.include_router(job.router, prefix="/jm")
    rt.include_router(ixp.router, prefix="/ixp")

    return rt

router = _build_router()
