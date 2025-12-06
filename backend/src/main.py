from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from fastapi.responses import ORJSONResponse

from src.common.db.database import db_helper
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
    await db_helper.dispose()


main_app = FastAPI(
    title="LightTask",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)
main_app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=True,
    )
