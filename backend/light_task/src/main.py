from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse

from src.config import settings
from src.db.database import db_helper
from src.errors import ErrorCode, normalize_error_detail, error_response
from src.logger import setup_logging, get_logger
from src.auth.router import router as auth_router
from src.boards.router import router as board_router
from src.projects.router import router as project_router
from src.users.router import router as user_router
from src.tags.router import router as tag_router
from src.invitations.router import router as invitation_router

logger = get_logger(__name__)

# модели импортируются для регистрации в metadata
from src.boards.models import BoardColumn, Task  # noqa: F401
from src.projects.models import Project, ProjectMember  # noqa: F401
from src.users.models import User  # noqa: F401
from src.tags.models import Tag  # noqa: F401
from src.invitations.models import ProjectInvitation  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    setup_logging()
    logger.info("Application startup")
    yield
    # shutdown
    logger.info("Application shutdown")
    await db_helper.dispose()


main_app = FastAPI(
    title="Kantano",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.run.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

main_app.include_router(auth_router, prefix="/api")
main_app.include_router(user_router, prefix="/api")
main_app.include_router(project_router, prefix="/api")
main_app.include_router(board_router, prefix="/api")
main_app.include_router(tag_router, prefix="/api")
main_app.include_router(invitation_router, prefix="/api")


@main_app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=normalize_error_detail(exc.detail),
        headers=exc.headers,
    )


@main_app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=error_response(ErrorCode.UNKNOWN_ERROR),
    )


@main_app.get("/api/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
