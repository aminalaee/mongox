import asyncio
import os
import typing

import bson
import pydantic
import pytest
from pymongo import errors

from mongox.database import Client
from mongox.exceptions import MultipleMatchesFound, NoMatchFound
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


def test_model_class() -> None:
    class Product(Model):
        sku: str

    with pytest.raises(AttributeError):
        product = Product(sku="12345")
        product.Meta.collection

    movie = Movie(name="Batman", year=2009)
    assert (
        movie.dict()
        == dict(movie)
        == {"name": "Batman", "year": 2009, "id": None, "uuid": None}
    )

    assert Movie.schema() == {
        "title": "Movie",
        "type": "object",
        "properties": {
            "_id": {"title": " Id", "type": "string"},
            "name": {"title": "Name", "type": "string"},
            "year": {"title": "Year", "type": "integer"},
            "uuid": {"title": "Uuid", "type": "string"},
        },
        "required": ["name", "year"],
    }


async def test_model_create_index() -> None:
    index_names = await Movie.create_indexes()
    assert index_names == ["name", "year_genre"]


async def test_model_insert() -> None:
    movie = await Movie(name="Forrest Gump", year=2003).insert()
    assert movie.name == "Forrest Gump"
    assert movie.year == 2003
    assert isinstance(movie.id, bson.ObjectId)

    with pytest.raises(pydantic.error_wrappers.ValidationError) as exc:
        await Movie(name="Avengers", year=2017, uuid="1").insert()
    assert exc.value.errors() == [
        {"loc": ("uuid",), "msg": "Invalid ObjectId", "type": "value_error"}
    ]

    with pytest.raises(errors.DuplicateKeyError):
        await Movie(name="Forrest Gump", year=2011).insert()


async def test_model_get() -> None:
    movie = await Movie.query().get()
    assert movie.name == "Forrest Gump"

    await Movie(name="Batman", year=2013).insert()

    movie = await Movie.query({Movie.name: "Forrest Gump"}).get()
    assert movie.name == "Forrest Gump"

    movie = await Movie.query({"_id": movie.id}).get()
    assert movie.name == "Forrest Gump"

    movie = await Movie.query({Movie.id: movie.id}).get()
    assert movie.name == "Forrest Gump"

    with pytest.raises(NoMatchFound):
        await Movie.query({Movie.name: "Interstellar"}).get()

    with pytest.raises(MultipleMatchesFound):
        await Movie.query().get()


async def test_model_first() -> None:
    movie = await Movie.query({Movie.name: "Avengers"}).first()
    assert movie is None

    movie = await Movie.query({Movie.name: "Batman"}).first()
    assert movie is not None
    assert movie.name == "Batman"


async def test_model_count() -> None:
    count = await Movie.query().count()
    assert count == 2

    count = await Movie.query({Movie.year: 2013}).count()
    assert count == 1


async def test_model_all() -> None:
    movies = await Movie.query().all()

    assert len(movies) == 2


async def test_model_sort() -> None:
    movies = await Movie.query().sort("name", Order.ASCENDING).all()

    assert movies[0].name == "Batman"
    assert movies[1].name == "Forrest Gump"

    movies = await Movie.query().sort(Movie.name, Order.ASCENDING).all()

    assert movies[0].name == "Batman"
    assert movies[1].name == "Forrest Gump"

    movies = await Movie.query().sort([(Movie.name, Order.DESCENDING)]).all()

    assert movies[0].name == "Forrest Gump"
    assert movies[1].name == "Batman"


async def test_model_skip() -> None:
    movies = await Movie.query().sort(Movie.name, Order.ASCENDING).skip(1).all()
    assert len(movies) == 1
    assert movies[0].name == "Forrest Gump"

    movie = await Movie.query().sort(Movie.name, Order.ASCENDING).skip(1).get()
    assert movie.name == "Forrest Gump"


async def test_model_limit() -> None:
    movies = await Movie.query().sort(Movie.name, Order.ASCENDING).limit(1).all()
    assert len(movies) == 1
    assert movies[0].name == "Batman"

    movies = (
        await Movie.query().sort(Movie.name, Order.ASCENDING).skip(1).limit(1).all()
    )
    assert len(movies) == 1
    assert movies[0].name == "Forrest Gump"


async def test_model_delete() -> None:
    count = await Movie.query({Movie.name: "Batman"}).delete()
    assert count == 1

    count = await Movie.query().delete()
    assert count == 1

    movie = await Movie(name="Batman", year=2007).insert()
    count = await movie.delete()
    assert count == 1


async def test_model_update_save() -> None:
    await Movie(name="Downfall", year=2002).insert()

    movie = await Movie.query().get()
    movie.year = 2003
    await movie.save()

    movie = await Movie.query().get()
    assert movie.year == 2003

    movie.year = movie.year + 1
    await movie.save()

    movie = await Movie.query().get()
    assert movie.year == 2004


async def test_model_bulk_update() -> None:
    await Movie(name="Boyhood", year=2004).insert()

    movies = await Movie.query({Movie.year: 2004}).update({Movie.year: 2010})
    assert movies[0].year == 2010
    assert movies[1].year == 2010

    movies = await Movie.query().all()
    assert movies[0].year == 2010
    assert movies[1].year == 2010


async def test_model_query_builder() -> None:
    await Movie(name="The Two Towers", year=2002).insert()
    await Movie(name="Casablanca", year=1942).insert()
    await Movie(name="Gone with the wind", year=1939).insert()

    movie = await Movie.query(Movie.year != 1920).first()
    assert movie is not None

    movie = await Movie.query(Movie.year == 1939).get()
    assert movie.name == "Gone with the wind"

    movie = await Movie.query(Movie.year < 1940).get()
    assert movie.name == "Gone with the wind"
    assert movie.year == 1939

    movie = await Movie.query(Movie.year <= 1939).get()
    assert movie.name == "Gone with the wind"
    assert movie.year == 1939

    movie = await Movie.query(Movie.year > 2000).first()
    assert movie is not None
    assert movie.name == "Downfall"
    assert movie.year == 2010

    movie = await Movie.query(Movie.year >= 1940).first()
    assert movie is not None
    assert movie.name == "Downfall"
    assert movie.year == 2010

    movie = (
        await Movie.query(Movie.name == "Casablanca").query(Movie.year == 1942).get()
    )
    assert movie.name == "Casablanca"
    assert movie.year == 1942

    assert (
        await Movie.query(Movie.name == "Casablanca").query(Movie.year == 1942).get()
        == await Movie.query(Movie.name == "Casablanca", Movie.year == 1942).get()
    )
