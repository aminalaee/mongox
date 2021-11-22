import copy
import typing

import pydantic

from mongox.database import Collection
from mongox.exceptions import InvalidKeyException, MultipleMatchesFound, NoMatchFound
from mongox.expressions import QueryExpression, SortExpression
from mongox.fields import ModelField, ObjectId
from mongox.index import Index, Order

T = typing.TypeVar("T", bound="Model")

__all__ = ["Model", "Q"]


class Q:
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

    async def all(self) -> typing.List[T]:
        """
        Fetch all documents matching the criteria
        """

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
        """
        Get count of documents matching the criteria
        """

        filter_query = QueryExpression.compile_many(self._filter)
        return await self._collection.count_documents(filter_query)

    async def delete(self) -> int:
        """
        Delete documents matching the criteria
        """

        filter_query = QueryExpression.compile_many(self._filter)
        result = await self._collection.delete_many(filter_query)
        return result.deleted_count

    async def first(self) -> typing.Optional[T]:
        """
        Get first document matching the criteria or None
        """

        objects = await self.limit(1).all()
        if not objects:
            return None
        return objects[0]

    async def get(self) -> T:
        """
        Get the only document matching or throw exceptions
        """

        objects = await self.limit(2).all()
        if len(objects) == 0:
            raise NoMatchFound()
        elif len(objects) == 2:
            raise MultipleMatchesFound()
        return objects[0]

    def limit(self, count: int = 0) -> "QuerySet[T]":
        """
        Limit query results
        """

        self._limit_count = count
        return self

    def query(
        self, *args: typing.Union[bool, typing.Dict, QueryExpression]
    ) -> "QuerySet[T]":
        """
        Filter query criteria
        """

        for arg in args:
            assert isinstance(arg, (dict, QueryExpression)), "Invalid argument to Query"
            if isinstance(arg, dict):
                query_expressions = QueryExpression.unpack(arg)
                self._filter.extend(query_expressions)
            else:
                self._filter.append(arg)

        return self

    def skip(self, count: int = 0) -> "QuerySet[T]":
        """
        Skip N number of documents
        """

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
        """
        Sort by (key, direction) or [(key, direction)]
        """

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

    async def update(self, *args: typing.Dict) -> typing.List[T]:
        """
        Update the matching criteria with provided info
        """

        kwargs = {}
        filter_: typing.List[QueryExpression] = []

        for arg in args:
            for key, value in arg.items():
                if isinstance(key, ModelField):
                    key = key.name
                kwargs[key] = value

            query_expression = QueryExpression(key, "$eq", value)
            filter_.append(query_expression)

        filter_query = QueryExpression.compile_many(self._filter)
        await self._collection.update_many(filter_query, {"$set": kwargs})

        self._filter = filter_

        return await self.all()


class Meta(pydantic.BaseConfig):
    collection: Collection
    indexes: typing.List[Index]


class ModelMetaClass(pydantic.main.ModelMetaclass):
    __fields__: typing.Dict[str, pydantic.fields.ModelField]

    @typing.no_type_check
    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        new_fields: typing.Dict[str, pydantic.fields.ModelField] = {}

        for field_name, field in cls.__fields__.items():
            # Swapping pydantic ModelField with MongoX ModelField
            new_field = copy.deepcopy(field)
            new_field.__class__ = ModelField
            new_fields[field_name] = new_field

        cls.__fields__ = new_fields
        return cls

    def __getattribute__(self, name: str) -> typing.Any:
        try:
            return super().__getattribute__(name)
        except AttributeError as exc:
            if name not in self.__fields__:
                raise exc
            return self.__fields__[name]


class Model(pydantic.BaseModel, metaclass=ModelMetaClass):
    Meta: typing.ClassVar[Meta]

    id: typing.Optional[ObjectId] = pydantic.Field(alias="_id")

    class Config:
        validate_assignment = True

    async def insert(self: T) -> T:
        """
        Insert the document
        """

        data = self.dict(exclude={"id"})
        result = await self.Meta.collection._collection.insert_one(data)
        self.id = result.inserted_id
        return self

    @classmethod
    async def create_index(cls, name: str) -> str:
        """
        Create single index from Meta indexes by name.

        Can raise `pymongo.errors.OperationFailure`.
        """

        for index in cls.Meta.indexes:
            if index.name == name:
                await cls.Meta.collection._collection.create_indexes([index])
                return index.name
        raise InvalidKeyException(f"Unable to find index: {name}")

    @classmethod
    async def create_indexes(cls) -> typing.List[str]:
        """
        Create indexes defined for the collection
        """

        return await cls.Meta.collection._collection.create_indexes(cls.Meta.indexes)

    async def delete(self) -> int:
        result = await self.Meta.collection._collection.delete_one({"_id": self.id})
        return result.deleted_count

    @classmethod
    async def drop_index(cls, name: str) -> str:
        """
        Drop single index from Meta indexes by name.

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
        """
        Drop all indexes defined for the collection.
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
        """
        Filter query criteria
        """

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
        """
        Save the document.

        This is equivalent of an update.
        """

        await self.Meta.collection._collection.update_one(
            {"_id": self.id}, {"$set": self.dict(exclude={"id", "_id"})}
        )
        for k, v in self.dict(exclude={"id"}).items():
            setattr(self, k, v)
        return self
