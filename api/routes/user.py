from fastapi import APIRouter, HTTPException
from sqlmodel import select

from api.core.log import get_logger
from api.database import NewSession
from api.models import User

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger("api.routes.user")


@router.get(
    "/{id}",
    description="Get user by ID",
)
async def get_user(
    id: int,
    session: NewSession,
) -> User:
    try:
        statement = select(User).where(User.id == id)
        result = await session.exec(statement)
        user = result.first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except HTTPException:
        # Re-raise HTTP exceptions (404, etc.) - these are not errors
        raise
    except Exception as e:
        # Only log actual errors
        logger.error(f"GET /users/{id} - Error: {str(e)}", exc_info=True)
        raise
