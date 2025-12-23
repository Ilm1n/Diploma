from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from light_task.src.config import settings
from light_task.src.db.database import db_helper
from light_task.src.auth.router import router as auth_router
from light_task.src.boards.router import router as board_router
from light_task.src.projects.router import router as project_router
from light_task.src.users.router import router as user_router
from light_task.src.tags.router import router as tag_router
from light_task.src.invitations.router import router as invitation_router

# модели импортируются для регистрации в metadata
from light_task.src.boards.models import BoardColumn, Task  # noqa: F401
from light_task.src.projects.models import Project, ProjectMember  # noqa: F401
from light_task.src.users.models import User  # noqa: F401
from light_task.src.tags.models import Tag  # noqa: F401
from light_task.src.invitations.models import ProjectInvitation  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await db_helper.dispose()


main_app = FastAPI(
    title="LightTask",
    version="0.1.0",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]

main_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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


@main_app.get("/")
async def root():
    return {"message": "LightTask API is running"}


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
