from abc import abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

from api.models.schema.misc.jsonable import JsonModel

_G = TypeVar("_G")
_DTO = TypeVar("_DTO")


class DTOsBase(JsonModel, Generic[_DTO]):
    __dto__: type[_DTO] | None = None

    items: Sequence[_DTO]

    @classmethod
    @abstractmethod
    async def from_objs(cls: type[_G], models: Sequence[_DTO]) -> _G:
        pass
