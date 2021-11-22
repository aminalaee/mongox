import asyncio
import os
import typing

import pytest

from mongox.database import Client
from mongox.exceptions import InvalidKeyException
from mongox.fields import ObjectId
from mongox.index import Index, IndexType, Order
from mongox.models import Model

pytestmark = pytest.mark.asyncio

database_uri = os.environ.get("DATABASE_URI", "mongodb://localhost:27017")
client = Client(database_uri, get_event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")


class Movie(Model):
    name: str
    year: int
    uuid: typing.Optional[ObjectId]

    class Meta:
        collection = db.get_collection("movies")
        indexes = [
            Index("name", unique=True),
            Index(keys=[("year", Order.DESCENDING), ("genre", IndexType.HASHED)]),
        ]


async def test_create_indexes() -> None:
    index_names = await Movie.create_indexes()
    assert index_names == ["name", "year_genre"]

    await Movie.drop_indexes()

    index = await Movie.create_index("name")
    assert index == "name"

    with pytest.raises(InvalidKeyException):
        await Movie.create_index("random_index")


async def test_drop_index() -> None:
    await Movie.drop_index("name")

    with pytest.raises(InvalidKeyException):
        await Movie.drop_index("random_index")


async def test_drop_indexes() -> None:
    await Movie.create_indexes()

    index_names = await Movie.drop_indexes()
    assert index_names == ["name", "year_genre"]

    await Movie.create_indexes()

    await Movie.drop_indexes(force=True)
