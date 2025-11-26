from abc import ABC
from collections.abc import Callable
from typing import Any, Final, TypeVar

from sqlalchemy import event
from sqlalchemy.engine.base import Connection
from sqlalchemy.orm.mapper import Mapper
from sqlmodel import SQLModel

_TableModel = TypeVar("_TableModel", bound=SQLModel)


class _on_event_base(ABC):
    __hijack_events_key__: Final[str] = "__hijack_events__"

    def inject_event(self) -> Callable[[], None]:
        def _self_getter() -> None:
            raise NotImplementedError("This should not be called.")

        setattr(_self_getter, self.__hijack_events_key__, self)
        return _self_getter


class _on_commit(_on_event_base):
    def __init__(self, name: str) -> None:
        self.name = name
        self.func: Callable[[Any, Any], Any] | None = None

    def __call__(
        self,
        func: Callable[[Any, Any], Any],
    ) -> Callable[[], None]:
        self.func = func
        return self.inject_event()


class _on_load(_on_event_base):
    def __init__(self) -> None:
        self.func: Callable[[Any], None] | None = None

    def __call__(
        self,
        func: Callable[[Any], None],
    ) -> Callable[[], None]:
        self.func = func
        return self.inject_event()


class hijack_events:
    def __init__(self, cls_: type[SQLModel]) -> None:
        self.cls_ = cls_

    @classmethod
    def register_table(cls, cls_: type[_TableModel]) -> type[_TableModel]:
        on_commit_events: list[_on_commit] = []
        on_load_events: list[_on_load] = []

        for attr_name in dir(cls_):
            attr = getattr(cls_, attr_name)
            attr_event_key: _on_event_base | None = getattr(
                attr, _on_event_base.__hijack_events_key__, None
            )
            if attr_event_key is None:
                continue

            match attr_event_key:
                case _on_load():
                    on_load_events.append(attr_event_key)
                case _on_commit():
                    on_commit_events.append(attr_event_key)

        if on_commit_events:

            @event.listens_for(cls_, "before_update")
            def _before_update_event(
                mapper: Mapper,
                connection: Connection,
                target: _TableModel,
            ) -> None:
                for updator in on_commit_events:
                    received_value = getattr(target, updator.name)
                    assert updator.func is not None
                    updated_value = updator.func(target, received_value)
                    setattr(target, updator.name, updated_value)

        if on_load_events:

            @event.listens_for(cls_, "load", restore_load_context=True)
            def _on_load_event(
                target: _TableModel,
                _: Any,
            ) -> None:
                for loader in on_load_events:
                    assert loader.func is not None
                    loader.func(target)

        return cls_

    @staticmethod
    def on_commit(name: str) -> _on_commit:
        return _on_commit(name)

    @staticmethod
    def on_load(cache: bool = False) -> _on_load:
        # TODO: cache implementation in the session
        del cache
        return _on_load()
