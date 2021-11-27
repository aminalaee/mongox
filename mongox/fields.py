import typing

import bson
import pydantic

from mongox.exceptions import InvalidKeyException
from mongox.expressions import QueryExpression

if typing.TYPE_CHECKING:  # pragma: no cover
    from mongox.models import EmbeddedModel, Model

Field = pydantic.Field

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

    def __init__(
        self,
        pydantic_field: pydantic.fields.ModelField,
        model_cls: typing.Type[typing.Union["EmbeddedModel", "Model"]] = None,
        parent: typing.Optional["ModelField"] = None,
    ):
        self._model_cls = model_cls
        self._pydantic_field = pydantic_field
        self._parent = parent

    @property
    def _name(self) -> str:
        if self._parent:
            return self._parent._name + "." + self._pydantic_field.alias
        return self._pydantic_field.alias

    def __lt__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self._name, "$lt", other)

    def __le__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self._name, "$lte", other)

    def __eq__(self, other: typing.Any) -> QueryExpression:  # type: ignore[override]
        # Using $eq instead of simple dict to allow regex
        return QueryExpression(self._name, "$eq", other)

    def __ne__(self, other: typing.Any) -> QueryExpression:  # type: ignore[override]
        return QueryExpression(self._name, "$ne", other)

    def __gt__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self._name, "$gt", other)

    def __ge__(self, other: typing.Any) -> QueryExpression:
        return QueryExpression(self._name, "$gte", other)

    def __hash__(self) -> int:
        return super().__hash__()

    def __getattr__(self, name: str) -> typing.Any:
        """
        Overriding attr to assign parent for reverse lookup
        """
        assert self._model_cls is not None

        if name not in self._model_cls.__mongox_fields__:
            raise InvalidKeyException(
                f"Model '{self._model_cls.__name__}' has no attribute '{name}'"
            )

        child_field: ModelField = self._model_cls.__mongox_fields__[name]
        return ModelField(
            pydantic_field=child_field._pydantic_field,
            model_cls=child_field._model_cls,
            parent=self,
        )
