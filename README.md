# MongoX

<p>
<a href="https://github.com/aminalaee/mongox/actions">
    <img src="https://github.com/aminalaee/mongox/workflows/Test%20Suite/badge.svg" alt="Build Status">
</a>
<a href="https://github.com/aminalaee/mongox/actions">
    <img src="https://github.com/aminalaee/mongox/workflows/publish/badge.svg" alt="Publish Status">
</a>
<a href="https://codecov.io/gh/aminalaee/mongox">
    <img src="https://codecov.io/gh/aminalaee/mongox/branch/main/graph/badge.svg" alt="Coverage">
</a>
<a href="https://pypi.org/project/mongox/">
    <img src="https://badge.fury.io/py/mongox.svg" alt="Package version">
</a>
</p>

MongoX is an async python ODM (Object Document Mapper) for MongoDB
which is built on top [Motor][motor] and [Pydantic][pydantic].

The main features include:

* Fully type annotated
* Async support Python 3.6+ (since it's built on top of Motor)
* Elegant editor support (since it's built on top of Pydantic)
* Autocompletion everywhere, from object creation to query results
* Custom query builder which is more intuitive and pythonic
* 100% test coverage

MongoX models are at the same time Pydantic models and have the same functionalitties,
so you can use them with your existing Pydantic models.

---

**Documentation**: [https://aminalaee.github.io/mongox](https://aminalaee.github.io/mongox)

---

## Installation

```shell
$ pip install mongox
```

---

## Quickstart

You can define `mongox` models the same way you define Pydantic models.
The difference is they should inherit from `mongox.Model` now:

```python
import asyncio

import mongox

client = Client(database_uri, get_event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")


class Movie(mongox.Model):
    name: str
    year: int

    class Meta:
        collection = db.get_collection("movies")
```

Now you can create some instances and insert them into the database:

```python
movie = await Movie(name="Forrest Gump", year=1994).insert()
```

The returned result will be a `Movie` instance, and also
`mypy` will understand that the `insert` will return a `Movie` instance.
So you will have type hints everywhere:

IMAGE HERE

Now you can fetch some data from the database.

You can use the same pattern as Pymongo/Motor:

```python
movie = await Movie.query({"name": "Forrest Gump"}).get()
```

Here the result returned will be a `Movie` instance and also
`mypy` will understand that the `get` method will return a `Movie`.
This will have great IDE support, autocompletion and validation.

IMAGE HERE

Or you can use `Movie` fields instead of dictionaries in the query (less room for bugs):

```python
movie = await Movie.query({Movie.name: "Forrest Gump"}).get()
```

And finally you can use a more intuitive query:

```python
movie = await Movie.query(Movie.name == "Forrest Gump").get()
```

Notice how we omitted the dictionary and passed the `Movie` fields in comparison.

Please refer to the documentation for full features.

[motor]: https://github.com/mongodb/motor
[pydantic]: https://github.com/samuelcolvin/pydantic
