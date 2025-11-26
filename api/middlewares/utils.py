import functools
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from typing_extensions import TypeAlias

_CallNext: TypeAlias = Callable[[Request], Awaitable[Response]]


def pass_through_preflight_request(
    func: Callable[[Any, Request, _CallNext], Awaitable[Response]]
) -> Callable[[Any, Request, _CallNext], Awaitable[Response],]:
    """
    Pass through preflight request
    """

    @functools.wraps(func)
    async def wrapper(self: Any, request: Request, call_next: _CallNext) -> Response:
        """
        Pass through preflight request
        """
        if request.method == "OPTIONS":
            return await call_next(request)

        return await func(self, request, call_next)

    return wrapper
