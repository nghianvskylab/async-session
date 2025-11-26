from contextvars import ContextVar

request_id: ContextVar[str] = ContextVar("request_id", default="")
user_id: ContextVar[str] = ContextVar("user_id", default="")
api_path: ContextVar[str] = ContextVar("api_path", default="")
