import asyncio
import typing

from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorDatabase,
)


class Collection:
    """
    MongoDB Collection with a referrence to the Motor Collection
    """

    def __init__(self, collection: AsyncIOMotorCollection, name: str) -> None:
        self._collection = collection
        self.name = name


class Database:
    """
    MongoDB Database with a referrence to the Motor database
    """

    def __init__(self, db: AsyncIOMotorDatabase, name: str) -> None:
        self._db = db
        self.name = name

    def get_collection(self, name: str) -> Collection:
        collection = self._db.get_collection(name)
        return Collection(collection, name)

    async def list_collections(self) -> typing.List[Collection]:
        collections = await self._db.list_collection_names()
        return list(map(self.get_collection, collections))


class Client:
    """
    MongoDB Client class with a referrence to the Motor client.
    """

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        get_event_loop: typing.Callable[[], asyncio.AbstractEventLoop] = None,
    ) -> None:
        self._client = AsyncIOMotorClient(uri)
        if get_event_loop:
            self._client.get_io_loop = get_event_loop

    @property
    def address(self) -> typing.Tuple[str, int]:
        return self._client.address

    @property
    def host(self) -> str:
        return self._client.HOST

    @property
    def port(self) -> int:
        return self._client.PORT

    async def drop_database(self, db: typing.Union[str, Database]) -> None:
        if isinstance(db, Database):
            await self._client.drop_database(db._db)
        else:
            await self._client.drop_database(db)

    def get_database(self, name: str) -> Database:
        db = self._client.get_database(name)
        return Database(db, name)

    async def list_databases(self) -> typing.List[Database]:
        databases = await self._client.list_database_names()
        return list(map(self.get_database, databases))
