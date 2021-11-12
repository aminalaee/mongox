import copy
import typing

import pydantic

from mongox.database import Collection
from mongox.exceptions import MultipleMatchesFound, NoMatchFound
from mongox.fields import ModelField, ObjectId
from mongox.index import Index, Order

T = typing.TypeVar("T", bound="Model")

__all__ = ["Model"]


class Query:
    @classmethod
    def _map_model_field(cls, field: typing.Union[str, ModelField]) -> str:
        if isinstance(field, ModelField):
            return field.alias
        return field

    @typing.overload
    @classmethod
    def _map(
        cls,
        kwargs: typing.Dict[str, typing.Any],
    ) -> typing.Dict[str, typing.Any]:  # pragma: no cover
        ...

    @typing.overload
    @classmethod
    def _map(
        cls,
        kwargs: typing.Dict[ModelField, typing.Any],
    ) -> typing.Dict[str, typing.Any]:  # pragma: no cover
        ...

    @classmethod
    def _map(
        cls,
        kwargs: typing.Dict,
    ) -> typing.Dict[str, typing.Any]:
        query: typing.Dict[str, typing.Any] = {}
        for key, value in kwargs.items():
            query[cls._map_model_field(key)] = value
        return query


class QuerySet(typing.Generic[T]):
    def __init__(
        self,
        cls_model: typing.Type[T],
        kwargs: typing.Dict[str, typing.Any] = None,
    ) -> None:
        self._cls_model = cls_model
        self._collection = cls_model.Meta.collection._collection
        self._filter: typing.Dict[str, typing.Any] = kwargs or {}
        self._limit_count = 0
        self._skip_count = 0
        self._sort: list = []

    async def all(self) -> typing.List[T]:
        """
        Fetch all documents matching the criteria
        """

        cursor = self._collection.find(self._filter)

        if self._sort:
            cursor = cursor.sort(self._sort)

        if self._skip_count:
            cursor = cursor.skip(self._skip_count)

        if self._limit_count:
            cursor = cursor.limit(self._limit_count)

        return [self._cls_model(**document) async for document in cursor]

    async def count(self) -> int:
        """
        Get count of documents matching the criteria
        """

        return await self._collection.count_documents(self._filter)

    async def delete(self) -> int:
        """
        Delete documents matching the criteria
        """

        result = await self._collection.delete_many(self._filter)
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

    def query(self, *args: typing.Union[bool, typing.Dict]) -> "QuerySet[T]":
        """
        Filter query criteria
        """

        for arg in args:
            assert isinstance(arg, dict), "Invalid argument to Query"
            self._filter.update(Query._map(arg))

        return self

    def skip(self, count: int = 0) -> "QuerySet[T]":
        """
        Skip N number of documents
        """

        self._skip_count = count
        return self

    @typing.overload
    def sort(self, key: str, direction: Order) -> "QuerySet[T]":  # pragma: no cover
        ...

    @typing.overload
    def sort(
        self, key: ModelField, direction: Order
    ) -> "QuerySet[T]":  # pragma: no cover
        ...

    @typing.overload
    def sort(
        self, key: typing.List[typing.Tuple[str, Order]]
    ) -> "QuerySet[T]":  # pragma: no cover
        ...

    @typing.overload
    def sort(
        self, key: typing.List[typing.Tuple[ModelField, Order]]
    ) -> "QuerySet[T]":  # pragma: no cover
        ...

    def sort(
        self, key: typing.Any, direction: typing.Optional[Order] = None
    ) -> "QuerySet[T]":
        """
        Sort by (key, direction) or [(key, direction)]
        """

        criteria = []
        direction = direction or Order.ASCENDING

        if isinstance(key, list):
            for key_dir in key:
                k, d = key_dir
                criteria.append((Query._map_model_field(k), d))
        else:
            criteria = [(Query._map_model_field(key), direction)]

        self._sort.append(*criteria)
        return self

    async def update(self, *args: typing.Dict) -> typing.List[T]:
        """
        Update the matching criteria with provided info
        """

        kwargs = {}
        for arg in args:
            kwargs.update(Query._map(arg))

        await self._collection.update_many(self._filter, {"$set": kwargs})

        self._filter = kwargs

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

    async def insert(self: T) -> T:
        """
        Insert the document
        """

        data = self.dict(exclude={"id"})
        result = await self.Meta.collection._collection.insert_one(data)
        self.id = result.inserted_id
        return self

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
    def query(
        cls: typing.Type[T], *args: typing.Union[bool, typing.Dict]
    ) -> QuerySet[T]:
        """
        Filter query criteria
        """

        kwargs: typing.Dict = {}
        if not args:
            return QuerySet(cls_model=cls, kwargs=kwargs)

        for arg in args:
            assert isinstance(arg, dict), "Invalid argument to Query"
            kwargs.update(Query._map(arg))

        return QuerySet(cls_model=cls, kwargs=kwargs)

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
