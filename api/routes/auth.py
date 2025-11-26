from api.config.api_router import CoreAPIRoute
from api.routes.users import user_common_router
from fastapi import APIRouter

# Router for regular users (prefix /users)
users_router = APIRouter(
    prefix="/users",
    tags=["User"],
    route_class=CoreAPIRoute,
)

users_router.include_router(user_common_router)
