from pydantic import BaseModel
from pydantic_core import SchemaValidator


def check_schema(model: BaseModel) -> None:
    """
    Revalidate the schema of the model.
    """
    schema_validator = SchemaValidator(schema=model.__pydantic_core_schema__)
    schema_validator.validate_python(model.__dict__)
