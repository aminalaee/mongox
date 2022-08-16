<p align="center">
<a href="https://github.com/aminalaee/mongox">
    <img width="420px" src="https://raw.githubusercontent.com/aminalaee/mongox/main/docs/assets/images/banner.png" alt"MongoX">
</a>
</p>

<p align="center">
<a href="https://github.com/aminalaee/mongox/actions">
    <img src="https://github.com/aminalaee/mongox/workflows/Test%20Suite/badge.svg" alt="Build Status">
</a>
<a href="https://github.com/aminalaee/mongox/actions">
    <img src="https://github.com/aminalaee/mongox/workflows/Publish/badge.svg" alt="Publish Status">
</a>
<a href="https://codecov.io/gh/aminalaee/mongox">
    <img src="https://codecov.io/gh/aminalaee/mongox/branch/main/graph/badge.svg" alt="Coverage">
</a>
<a href="https://pypi.org/project/mongox/">
    <img src="https://badge.fury.io/py/mongox.svg" alt="Package version">
</a>
<a href="https://pypi.org/project/mongox" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/mongox.svg?color=%2334D058" alt="Supported Python versions">
</a>
</p>

---

# MongoX

MongoX is an async python ODM (Object Document Mapper) for MongoDB
which is built on top of [Motor][motor] and [Pydantic][pydantic].

The main features include:

* Fully type annotated
* Async support Python 3.7+ (since it's built on top of Motor)
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

client = mongox.Client("mongodb://localhost:27017")
db = client.get_database("test_db")


class Movie(mongox.Model, db=db, collection="movies"):
    name: str
    year: int
```

Now you can create some instances and insert them into the database:

```python
movie = await Movie(name="Forrest Gump", year=1994).insert()
```

The returned result will be a `Movie` instance, and `mypy`
will understand that this is a `Movie` instance.
So you will have type hints and validations everywhere.

Now you can fetch some data from the database.

You can use the same pattern as PyMongo/Motor:

```python
movie = await Movie.query({"name": "Forrest Gump"}).get()
```

Or you can use `Movie` fields instead of dictionaries in the query (less room for bugs):

```python
movie = await Movie.query({Movie.name: "Forrest Gump"}).get()
```

And finally you can use a more intuitive query (limited yet):

```python
movie = await Movie.query(Movie.name == "Forrest Gump").get()
```

Notice how we omitted the dictionary and passed the `Movie` fields in comparison.

---

Please refer to the documentation [here](https://aminalaee.github.io/mongox) or the full examples [here](https://github.com/aminalaee/mongox/tree/main/examples).

---

[motor]: https://github.com/mongodb/motor
[pydantic]: https://github.com/samuelcolvin/pydantic
