import asyncio
import os

import pytest

from mongox.database import Client

pytestmark = pytest.mark.asyncio

database_uri = os.environ.get("DATABASE_URI", "mongodb://localhost:27017")
client = Client(database_uri, get_event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")
collection = db.get_collection("movies")


async def test_client_class() -> None:
    assert client.host == "localhost"
    assert client.port == 27017
    assert client.address == ("localhost", 27017)

    await client.drop_database("sample")
    await client.drop_database(db)

    databases = await client.list_databases()
    assert "admin" in [db.name for db in databases]


async def test_database_class() -> None:
    collection = await db._db.create_collection("movies")

    collections = await db.list_collections()
    assert collections[0].name == collection.name
