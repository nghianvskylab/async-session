from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from api.config.api_router import CoreAPIRoute
from api.config.database import db_engine
from api.config.log import get_logger, setup_logging
from api.config.settings import settings
from api.exceptions.handler import (
    global_exception_handler,
    validation_exception_handler,
)
from api.routes.admin import admin_router
from api.routes.auth import users_router
from fastapi import FastAPI, Response
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_core import ValidationError

setup_logging()
logger = get_logger("api.main")

IS_PROD = not settings.DEBUG


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for FastAPI app."""
    try:
        yield
    except Exception as e:
        logger.error(f"Error in application lifecycle: {str(e)}", exc_info=True)
        raise
    finally:
        try:
            await db_engine.dispose()
        except Exception as e:
            logger.error(f"Error disposing database engine: {str(e)}", exc_info=True)


app = FastAPI(
    title=settings.APP_NAME,
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/re-docs",
    openapi_url=None if IS_PROD else "/openapi.json",
    lifespan=lifespan,
    description="Fast Api",
    version=settings.APP_VERSION,
)

app.router.route_class = CoreAPIRoute

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, global_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)

app.include_router(admin_router)
app.include_router(users_router)


@app.get("/_health", include_in_schema=False)
def health_check() -> Response:
    """Health check endpoint."""
    return Response(status_code=200)
