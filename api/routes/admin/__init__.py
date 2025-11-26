from api.config.api_router import CoreAPIRoute
from api.exceptions.base import get_exceptions_schema
from api.routes.admin.users import users_router
from fastapi import APIRouter

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    route_class=CoreAPIRoute,
    responses=get_exceptions_schema(preset="uca"),
)

admin_router.include_router(users_router)
