import asyncio

import mongox


client = mongox.Client(
    "mongodb://localhost:27017", get_event_loop=asyncio.get_running_loop
)
db = client.get_database("test_db")


class Movie(mongox.Model, db=db):
    name: str
    year: int = mongox.Field(gt=1800, lt=2050)


async def main():
    await Movie(name="Forrest Gump", year=1994).insert()

    movie = await Movie.query(Movie.name == "Forrest Gump").get()

    print(movie)

    movie.year = 1993
    movie = await movie.save()

    print(movie)

    await movie.delete()


asyncio.run(main())
