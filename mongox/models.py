import re
import typing

import bson
import pydantic

from mongox._helpers import normalize_class_name
from mongox.database import Collection, Database
from mongox.exceptions import (
    InvalidFieldTypeException,
    InvalidKeyException,
    InvalidObjectIdException,
    MultipleMatchesFound,
    NoMatchFound,
)
from mongox.expressions import QueryExpression, SortExpression
from mongox.fields import ModelField, ObjectId
from mongox.index import Index, Order

T = typing.TypeVar("T", bound="Model")

__all__ = ["EmbeddedModel", "Model", "Q"]


class Q:
    """Shortcut for creating QueryExpression."""

    @classmethod
    def asc(cls, key: typing.Any) -> SortExpression:
        return SortExpression(key, Order.ASCENDING)

    @classmethod
    def desc(cls, key: typing.Any) -> SortExpression:
        return SortExpression(key, Order.DESCENDING)

    @classmethod
    def in_(cls, key: typing.Any, values: typing.List) -> QueryExpression:
        return QueryExpression(key=key, operator="$in", value=values)

    @classmethod
    def not_in(cls, key: typing.Any, values: typing.List) -> QueryExpression:
        return QueryExpression(key=key, operator="$nin", value=values)

    @classmethod
    def and_(cls, *args: typing.Union[bool, QueryExpression]) -> QueryExpression:
        assert not isinstance(args, bool)
        return QueryExpression(key="$and", operator="$and", value=args)

    @classmethod
    def or_(cls, *args: typing.Union[bool, QueryExpression]) -> QueryExpression:
        assert not isinstance(args, bool)
        return QueryExpression(key="$or", operator="$or", value=args)

    @classmethod
    def contains(cls, key: typing.Any, value: typing.Any) -> QueryExpression:
        if key._pydantic_field.outer_type_ is str:
            return QueryExpression(key=key, operator="$regex", value=value)
        return QueryExpression(key=key, operator="$eq", value=value)

    @classmethod
    def regex(
        cls, key: typing.Any, value: typing.Union[str, re.Pattern]
    ) -> QueryExpression:
        if key._pydantic_field.outer_type_ is str:
            expression = value.pattern if isinstance(value, re.Pattern) else value
            return QueryExpression(key=key, operator="$regex", value=expression)
        name = key if isinstance(key, str) else key._name
        raise InvalidFieldTypeException(f"The {name} field is not of type str")


class QuerySet(typing.Generic[T]):
    def __init__(
        self,
        cls_model: typing.Type[T],
        filter_: typing.List[QueryExpression] = None,
    ) -> None:
        self._cls_model = cls_model
        self._collection = cls_model.Meta.collection._collection
        self._filter: typing.List[QueryExpression] = filter_ or []
        self._limit_count = 0
        self._skip_count = 0
        self._sort: typing.List[SortExpression] = []

    async def __aiter__(self) -> typing.AsyncGenerator[T, None]:
        """Allow iterating over queryset results."""

        filter_query = QueryExpression.compile_many(self._filter)
        cursor = self._collection.find(filter_query)

        async for document in cursor:
            yield self._cls_model(**document)

    async def all(self) -> typing.List[T]:
        """Fetch all documents matching the criteria."""

        filter_query = QueryExpression.compile_many(self._filter)
        cursor = self._collection.find(filter_query)

        if self._sort:
            sort_query = [expr.compile() for expr in self._sort]
            cursor = cursor.sort(sort_query)

        if self._skip_count:
            cursor = cursor.skip(self._skip_count)

        if self._limit_count:
            cursor = cursor.limit(self._limit_count)

        return [self._cls_model(**document) async for document in cursor]

    async def count(self) -> int:
        """Get count of documents matching the criteria."""

        filter_query = QueryExpression.compile_many(self._filter)
        return await self._collection.count_documents(filter_query)

    async def delete(self) -> int:
        """Delete documents matching the criteria."""

        filter_query = QueryExpression.compile_many(self._filter)
        result = await self._collection.delete_many(filter_query)
        return result.deleted_count

    async def first(self) -> typing.Optional[T]:
        """Get first document matching the criteria or None."""

        objects = await self.limit(1).all()
        if not objects:
            return None
        return objects[0]

    async def get(self) -> T:
        """Get the only document matching or throw exceptions."""

        objects = await self.limit(2).all()
        if len(objects) == 0:
            raise NoMatchFound()
        elif len(objects) == 2:
            raise MultipleMatchesFound()
        return objects[0]

    async def get_or_create(self, defaults: typing.Dict = dict()) -> T:
        """Get the only document matching or create the document."""

        data = {expression.key: expression.value for expression in self._filter}
        defaults = {
            (key if isinstance(key, str) else key._name): value
            for key, value in defaults.items()
        }

        values, _, validation_error = pydantic.validate_model(
            self._cls_model, {**defaults, **data}
        )

        if validation_error:
            raise validation_error

        model = await self._collection.find_one_and_update(
            data,
            {"$setOnInsert": values},
            upsert=True,
            return_document=True,
        )
        return self._cls_model(**model)

    def limit(self, count: int = 0) -> "QuerySet[T]":
        """Limit query results."""

        self._limit_count = count
        return self

    def query(
        self, *args: typing.Union[bool, typing.Dict, QueryExpression]
    ) -> "QuerySet[T]":
        """Filter query criteria."""

        for arg in args:
            assert isinstance(arg, (dict, QueryExpression)), "Invalid argument to Query"
            if isinstance(arg, dict):
                query_expressions = QueryExpression.unpack(arg)
                self._filter.extend(query_expressions)
            else:
                self._filter.append(arg)

        return self

    def skip(self, count: int = 0) -> "QuerySet[T]":
        """Skip N number of documents."""

        self._skip_count = count
        return self

    @typing.overload
    def sort(self, key: SortExpression) -> "QuerySet[T]":  # pragma: no cover
        ...

    @typing.overload
    def sort(
        self, key: typing.Any, direction: Order
    ) -> "QuerySet[T]":  # pragma: no cover
        ...

    @typing.overload
    def sort(
        self, key: typing.List[typing.Tuple[typing.Any, Order]]
    ) -> "QuerySet[T]":  # pragma: no cover
        ...

    def sort(
        self, key: typing.Any, direction: typing.Optional[Order] = None
    ) -> "QuerySet[T]":
        """Sort by (key, direction) or [(key, direction)]."""

        direction = direction or Order.ASCENDING

        if isinstance(key, list):
            for key_dir in key:
                sort_expression = SortExpression(*key_dir)
                self._sort.append(sort_expression)
        elif isinstance(key, (str, ModelField)):
            sort_expression = SortExpression(key, direction)
            self._sort.append(sort_expression)
        else:
            self._sort.append(key)

        return self

    async def update(self, **kwargs: typing.Any) -> typing.List[T]:
        """Update the matching criteria with provided info."""

        field_definitions = {
            name: (annotations, ...)
            for name, annotations in self._cls_model.__annotations__.items()
            if name in kwargs
        }

        if field_definitions:
            pydantic_model: typing.Type[pydantic.BaseModel] = pydantic.create_model(  # type: ignore # noqa: E501
                self._cls_model.__name__, **field_definitions
            )
            values, _, validation_error = pydantic.validate_model(
                pydantic_model, kwargs
            )

            if validation_error:
                raise validation_error

            filter_query = QueryExpression.compile_many(self._filter)
            await self._collection.update_many(filter_query, {"$set": values})

            _filter = [
                expression
                for expression in self._filter
                if expression.key not in values
            ]
            _filter.extend(
                [QueryExpression(key, "$eq", value) for key, value in values.items()]
            )

            self._filter = _filter
        return await self.all()


class Meta(pydantic.BaseConfig):
    database: Database
    collection: Collection
    indexes: typing.List[Index]


class ModelMetaClass(pydantic.main.ModelMetaclass):
    __mongox_fields__: typing.Dict[str, ModelField]

    @typing.no_type_check
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)

        if kwargs:
            cls.Meta = Meta()

            assert "db" in kwargs, "DB instance required"
            assert isinstance(kwargs["db"], Database)
            cls.Meta.database = kwargs["db"]

            collection_name = kwargs.get(
                "collection", normalize_class_name(cls.__name__) + "s"
            )
            cls.Meta.collection = kwargs["db"].get_collection(collection_name)
            cls.Meta.indexes = kwargs.get("indexes", [])

        mongox_fields: typing.Dict[str, ModelField] = {}

        for field_name, field in cls.__fields__.items():
            # Swapping pydantic ModelField with MongoX ModelField
            new_field = ModelField(pydantic_field=field, model_cls=field.type_)
            mongox_fields[field_name] = new_field

        cls.__mongox_fields__ = mongox_fields
        return cls

    def __getattr__(self, name: str) -> typing.Any:
        if name in self.__mongox_fields__:
            return self.__mongox_fields__[name]
        return super().__getattribute__(name)


class EmbeddedModelMetaClass(pydantic.main.ModelMetaclass):
    __mongox_fields__: typing.Dict[str, ModelField]

    @typing.no_type_check
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        mongox_fields: typing.Dict[str, ModelField] = {}

        for field_name, field in cls.__fields__.items():
            # Swapping pydantic ModelField with MongoX ModelField
            new_field = ModelField(pydantic_field=field, model_cls=cls)
            mongox_fields[field_name] = new_field

        cls.__mongox_fields__ = mongox_fields
        return cls


class EmbeddedModel(pydantic.BaseModel, metaclass=EmbeddedModelMetaClass):
    __mongox_fields__: typing.Dict[str, ModelField]

    class Config:
        validate_assignment = True


class Model(pydantic.BaseModel, metaclass=ModelMetaClass):
    __mongox_fields__: typing.Dict[str, ModelField]

    Meta: typing.ClassVar[Meta]
    id: typing.Optional[ObjectId] = pydantic.Field(alias="_id")

    class Config:
        validate_assignment = True
        json_encoders = {
            bson.ObjectId: str,
        }

    async def insert(self: T) -> T:
        """Insert the document."""

        data = self.dict(exclude={"id"})
        result = await self.Meta.collection._collection.insert_one(data)
        self.id = result.inserted_id
        return self

    @classmethod
    async def insert_many(cls: typing.Type[T], models: typing.List[T]) -> typing.List[T]:
        if not all(isinstance(model, cls) for model in models):
            raise TypeError(f"All models must be of type {cls.__name__}")

        data = (model.dict(exclude={"id"}) for model in models)
        results = await cls.Meta.collection._collection.insert_many(data)
        for model, inserted_id in zip(models, results.inserted_ids):
            model.id = inserted_id
        return models

    @classmethod
    async def create_index(cls, name: str) -> str:
        """Create single index from Meta indexes by name.

        Can raise `pymongo.errors.OperationFailure`.
        """

        for index in cls.Meta.indexes:
            if index.name == name:
                await cls.Meta.collection._collection.create_indexes([index])
                return index.name
        raise InvalidKeyException(f"Unable to find index: {name}")

    @classmethod
    async def create_indexes(cls) -> typing.List[str]:
        """Create indexes defined for the collection."""

        return await cls.Meta.collection._collection.create_indexes(cls.Meta.indexes)

    async def delete(self) -> int:
        """Delete the current document."""

        result = await self.Meta.collection._collection.delete_one({"_id": self.id})
        return result.deleted_count

    @classmethod
    async def drop_index(cls, name: str) -> str:
        """Drop single index from Meta indexes by name.

        Can raise `pymongo.errors.OperationFailure`.
        """

        for index in cls.Meta.indexes:
            if index.name == name:
                await cls.Meta.collection._collection.drop_index(name)
                return name
        raise InvalidKeyException(f"Unable to find index: {name}")

    @classmethod
    async def drop_indexes(
        cls, force: bool = False
    ) -> typing.Optional[typing.List[str]]:
        """Drop all indexes defined for the collection.

        With `force=True`, even indexes not defined on the collection will be removed.

        Can raise `pymongo.errors.OperationFailure`.
        """

        if force:
            return await cls.Meta.collection._collection.drop_indexes()

        index_names = [await cls.drop_index(index.name) for index in cls.Meta.indexes]
        return index_names

    @classmethod
    def query(
        cls: typing.Type[T], *args: typing.Union[bool, typing.Dict, QueryExpression]
    ) -> QuerySet[T]:
        """Filter query criteria."""

        filter_: typing.List[QueryExpression] = []
        if not args:
            return QuerySet(cls_model=cls)

        for arg in args:
            assert isinstance(arg, (dict, QueryExpression)), "Invalid argument to Query"
            if isinstance(arg, dict):
                query_expressions = QueryExpression.unpack(arg)
                filter_.extend(query_expressions)
            else:
                filter_.append(arg)

        return QuerySet(cls_model=cls, filter_=filter_)

    async def save(self: T) -> T:
        """Save the document.

        This is equivalent of a single instance update.
        """

        await self.Meta.collection._collection.update_one(
            {"_id": self.id}, {"$set": self.dict(exclude={"id", "_id"})}
        )
        for k, v in self.dict(exclude={"id"}).items():
            setattr(self, k, v)
        return self

    @classmethod
    async def get_by_id(cls: typing.Type[T], id: typing.Union[str, bson.ObjectId]) -> T:
        """Get document by id."""

        if isinstance(id, str):
            try:
                id = bson.ObjectId(id)
            except bson.errors.InvalidId as e:
                raise InvalidObjectIdException(
                    f'"{id}" is not a valid BSON ObjectId'
                ) from e

        return await cls.query({"_id": id}).get()
