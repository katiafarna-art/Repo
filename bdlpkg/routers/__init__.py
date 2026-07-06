from fastapi.applications import FastAPI

from bdlpkg.routers import internal


def register_routers(app: FastAPI) -> FastAPI:
    app.include_router(internal.router, prefix="/internal")
    return app