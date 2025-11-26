from collections.abc import Callable

from api.config.app_ctx import api_path, request_id
from api.config.log import get_logger
from asgi_correlation_id import correlation_id
from fastapi import Request, Response
from fastapi.routing import APIRoute

logger = get_logger("core")


class CoreAPIRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            _request_id = correlation_id.get()

            request.state.request_id = _request_id
            path = request.scope["root_path"] + request.scope["route"].path
            name = f"{request.method}:{path}"

            api_path.set(name)
            request_id.set(_request_id or "")

            if path.split("/")[-1].startswith("_"):
                # If the last path start with an underscore, it is a private endpoint
                # do nothing
                return await original_route_handler(request)

            # Log request without CloudWatch metrics for now
            logger.debug(f"Processing request: {name}")
            result = await original_route_handler(request)
            return result

        return custom_route_handler
