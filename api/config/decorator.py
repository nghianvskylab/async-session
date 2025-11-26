"""
Logging utilities for debugging and performance monitoring.
"""

import functools
import logging
import time
from typing import Any, Callable, ParamSpec, TypeVar, cast

P = ParamSpec("P")

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def execution_time(label: str | None = None) -> Callable[[F], F]:
    """
    Decorator to log execution time of functions.

    Args:
        label: Optional label to prefix the log message
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.time()
            result = await func(*args, **kwargs)
            end = time.time()
            duration = end - start
            prefix = f"[{label}] " if label else ""
            logger.info(f"{prefix}{func.__name__} executed in {duration:.4f} seconds")
            return result

        return cast(F, async_wrapper)

    return decorator


def log_input(label: str | None = None) -> Callable[[F], F]:
    """
    Decorator to log input parameters of functions for debugging.

    Args:
        label: Optional label to prefix the log message
    """

    def decorator(func: F) -> F:
        def _log_args(*args: Any, **kwargs: Any) -> None:
            func_name = func.__name__
            class_name = label.split(".")[0] if label and "." in label else "API"

            input_params: list[str] = []
            if args:
                args_to_log = (
                    args[1:]
                    if len(args) > 0 and hasattr(args[0], "__class__")
                    else args
                )
                if args_to_log:
                    input_params.append(f"args={args_to_log}")
            if kwargs:
                input_params.append(f"kwargs={kwargs}")
            input_str = ", ".join(input_params) if input_params else "no parameters"
            logger.info(f"[{class_name}] {func_name} INPUT: {input_str}")

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            _log_args(*args, **kwargs)
            return await func(*args, **kwargs)

        return cast(F, async_wrapper)

    return decorator
