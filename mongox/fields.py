import typing

import bson
from pydantic import Field
from pydantic.fields import ModelField as PydanticModelField

from mongox.expressions import QueryExpression

if typing.TYPE_CHECKING:  # pragma: no cover
    from mongox.models import Model

__all__ = ["Field", "ObjectId"]


class ObjectId(bson.ObjectId):
    """
    Pydantic ObjectId field with validators
    """

    @classmethod
    def __get_validators__(cls) -> typing.Generator[bson.ObjectId, None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: typing.Any) -> bson.ObjectId:
        if not bson.ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return bson.ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema: dict) -> None:
        field_schema.update(type="string")


class ModelField:
    """
    Custom ModelField to create query building
    """

    __slots__: typing.Tuple[str, ...] = ("mongox_model", "name", "pydantic_field")

    def __init__(
        self, mongox_model: "Model", pydantic_field: PydanticModelField
    ) -> None:
        self.mongox_model = mongox_model
        self.name = pydantic_field.alias
        self.pydantic_field = pydantic_field

    def __lt__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self.name, "$lt", other)

    def __le__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self.name, "$lte", other)

    def __eq__(self, other: typing.Any) -> QueryExpression:  # type: ignore[override]
        # Using $eq instead of simple dict to allow regex
        return QueryExpression(self.name, "$eq", other)

    def __ne__(self, other: typing.Any) -> QueryExpression:  # type: ignore[override]
        return QueryExpression(self.name, "$ne", other)

    def __gt__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self.name, "$gt", other)

    def __ge__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self.name, "$gte", other)

    def __hash__(self) -> int:
        return super().__hash__()
