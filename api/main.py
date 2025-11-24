from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.core.log import get_logger, setup_logging
from api.database import db_engine
from api.routes.user import router as user_router

# Setup logging
setup_logging()
logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup - no logging for normal startup
    try:
        yield
    except Exception as e:
        logger.error(f"Error in application lifecycle: {str(e)}", exc_info=True)
        raise
    finally:
        # Shutdown
        try:
            await db_engine.dispose()
        except Exception as e:
            logger.error(f"Error disposing database engine: {str(e)}", exc_info=True)


app = FastAPI(
    title="FastAPI Performance Test",
    description="Performance testing API with PostgreSQL",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(user_router)

