import asyncio
import os
import typing

import pytest

from mongox.database import Client
from mongox.exceptions import InvalidKeyException
from mongox.models import Model

pytestmark = pytest.mark.asyncio

database_uri = os.environ.get("DATABASE_URI", "mongodb://localhost:27017")
client = Client(database_uri, get_event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")


class MovieMultiple(Model, db=db, collection="movies_multiple"):
    name: str
    year: int


class BookMultiple(Model, db=db, collection="books_multiple"):
    title: str
    year: int


async def test_multiple_model() -> None:
    movie = await MovieMultiple(name="Forest Gump", year=1994).insert()
    book = await BookMultiple(title="1984", year=1949).insert()

    count = await MovieMultiple.query().count()
    assert count == 1

    count = await BookMultiple.query().count()
    assert count == 1
