from copy import deepcopy
from typing import Any, Generic, Optional, TypeVar, cast

from api.config.log import get_logger
from api.models.schema.misc.jsonable import JsonModel
from pydantic import create_model
from pydantic.fields import FieldInfo
from sqlmodel import SQLModel

logger = get_logger("database")

_B = TypeVar("_B", bound=SQLModel)


class FieldUpdateModel(Generic[_B]):
    def override_fields_in(self, base: _B) -> _B:
        query_fields = cast(JsonModel, self).model_dump(
            exclude_none=True,
            exclude_unset=True,
        )

        for field_name, field_value in query_fields.items():
            if hasattr(base, field_name):
                value = getattr(base, field_name)
                if value is None:  # Do not update None values
                    continue

                logger.debug(f"Updating {field_name} from {value} to {field_value}")
                setattr(base, field_name, field_value)
            else:
                raise AttributeError(
                    f"{base.__class__.__name__} has no attribute {field_name}"
                )

        return base


_M = TypeVar("_M", bound=FieldUpdateModel[Any])


def partial_model(model: type[_M]) -> type[_M]:
    """
    Convert given model to a partial model that can be
    used to update the fields of the original model.

    ```python
    @partial_model
    class UpdateProject(ProjectBase, FieldUpdateModel[Project]):
        # all fields will be shown as optional in the OpenAPI schema
        fields_that_exist_in_project_and_can_be_updated: str


    @user_only_project_select_router.put("")
    async def update_project_details(
        project: Annotated[Project, Depends(find_project)],
        update_project: UpdateProject,
        session: NewSession,
    ) -> ProjectDTO:
        # update fields in the project object with the values from update_project
        # fields will be compared with the openapi schema
        update_project.override_fields_in(project)
        await project.update(session)
        return await ProjectDTO.from_obj(project, session)
    ```
    """

    def make_field_optional(
        field: FieldInfo,
        default: Any | None = None,
    ) -> tuple[Any, FieldInfo]:
        new = deepcopy(field)
        new.default = default
        new.annotation = Optional[field.annotation]  # type: ignore
        return new.annotation, new

    model_cls = cast(type[JsonModel], model)

    return create_model(  # type: ignore
        model_cls.__name__,
        __base__=model_cls,  # type: ignore
        __module__=model_cls.__module__,
        **{  # type: ignore
            field_name: make_field_optional(field_info)
            for field_name, field_info in model_cls.model_fields.items()
        },
    )
