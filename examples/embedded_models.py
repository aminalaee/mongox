import asyncio

import mongox


client = mongox.Client(
    "mongodb://localhost:27017", get_event_loop=asyncio.get_running_loop
)
db = client.get_database("test_db")


class Genre(mongox.EmbeddedModel):
    name: str = mongox.Field(min_length=5)


class Movie(mongox.Model, db=db, collection="movies"):
    name: str
    genre: Genre


async def main():
    genre = Genre(name="Action")
    await Movie(name="Saving Private Ryan", genre=genre).insert()

    movie = await Movie.query(Movie.genre.name == "Action").get()

    print(movie)

    movie.genre.name = "History"
    movie = await movie.save()

    print(movie)

    await movie.delete()


asyncio.run(main())
