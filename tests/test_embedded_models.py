import asyncio
import os
import typing

import pytest

from mongox.database import Client
from mongox.exceptions import InvalidKeyException
from mongox.models import EmbeddedModel, Model

pytestmark = pytest.mark.asyncio

database_uri = os.environ.get("DATABASE_URI", "mongodb://localhost:27017")
client = Client(database_uri, get_event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")


class Award(EmbeddedModel):
    name: str


class Crew(EmbeddedModel):
    award: Award
    name: str


class Actor(EmbeddedModel):
    name: str


class Genre(EmbeddedModel):
    title: str


class Movie(Model):
    actors: typing.List[Actor]
    director: Crew
    name: str
    genre: Genre
    year: int

    class Meta:
        collection = db.get_collection("movies")


async def test_embedded_model() -> None:
    actor = Actor(name="Tom Hanks")
    genre = Genre(title="Action")
    award = Award(name="Academy Award")
    director = Crew(name="Steven Spielberg", award=award)

    await Movie(
        actors=[actor],
        name="Saving Private Ryan",
        director=director,
        year=1990,
        genre=genre,
    ).insert()

    movie = await Movie.query(Movie.genre.title == "Action").get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.genre == genre).get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.actors == [actor]).get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.director.award.name == "Academy Award").get()
    assert movie.name == "Saving Private Ryan"

    movie = await Movie.query(Movie.director.award == award).get()
    assert movie.name == "Saving Private Ryan"

    with pytest.raises(InvalidKeyException):
        await Movie.query(Movie.director.award.year == 1990).get()  # type: ignore
