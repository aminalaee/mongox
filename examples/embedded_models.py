import asyncio

import mongox


client = mongox.Client(
    "mongodb://localhost:27017", get_event_loop=asyncio.get_running_loop
)
db = client.get_database("test_db")


class Genre(mongox.EmbeddedModel):
    title: str = mongox.Field(min_length=5)


class Movie(mongox.Model):
    name: str
    genre: Genre

    class Meta:
        collection = db.get_collection("movies")


async def main():
    genre = Genre(title="Action")
    await Movie(name="Saving Private Ryan", genre=genre).insert()

    movie = await Movie.query(Movie.genre.title == "Action").get()

    print(movie)

    movie.genre.title = "History"
    movie = await movie.save()

    print(movie)

    await movie.delete()


asyncio.run(main())
