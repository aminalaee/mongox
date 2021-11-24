### Defining documents

As you probably already know, MongoDB databases have collections instead of tables.
And each collection has documents instead of rows.

You can define your documents by inheriting from `mongox.Model`.

```python
import asyncio

import mongox

client = mongox.Client(
    "mongodb://localhost:27017", get_event_loop=asyncio.get_running_loop
)
db = client.get_database("test_db")


class Movie(mongox.Model):
    name: str
    year: int

    class Meta:
        collection = db.get_collection("movies")
```

Model attributes are defined the same way as Pydantic. The `Movie` class
is both a mongox `Model` and also a pydantic `BaseModel`.

Now we have a `Movie` collection with attributes `name` and `year`.

!!! note
    The `Meta` class is required since we need to know which collection this belongs to.

### Field validation

You can add field-level validations by using `mongox.Field`.
This is actually just a short-cut to the Pydantic `Field` and accepts the same arguments.

Let's say we want to limit the `year` attribute of Movie to be more strict:

```python
import mongox


class Movie(mongox.Model):
    name: str
    year: int = mongox.Field(gt=1800)
```

Now when creating a `Movie` instance, the year will be validated differently.

This will be ok:

```python
await Movie(name="Forrest Gump", year=1994).insert()
```

But this will throw a Pydantic `ValidationError`:

```python
await Movie(name="Golden Oldie", year=1790).insert()

# E   pydantic.error_wrappers.ValidationError: 1 validation error for Movie
# E   year
# E     ensure this value is greater than 1800 (type=value_error.number.not_gt; limit_value=1800)
```

Some of the most common `Field` arguments include:

For numeric types like `int`, `float` and `Decimal`:

* `gt` Rquires the field to be greater than
* `ge` Rquires the field to be greater than or equal to
* `le` Rquires the field to be less than or equal to
* `lt` Rquires the field to be less than
* `multiple_of` Requires the field to be a multiple of

For strings:

* `min_length` Requires the field to have a minimum length
* `max_length` Requires the field to have a maximum length
* `regex` Requires the field to match a regular expression

For a full list of `Field` arguments you can refer to
the Pydantic docs [here](https://pydantic-docs.helpmanual.io/usage/schema/#field-customisation).

### Defining indexes

Index definition should be inside the `Meta` class of the Model.

```python
import mongox


class Movie(mongox.Model):
    name: str
    genre: str
    year: int

    class Meta:
        collection = db.get_collection("movies")
        indexes = [
            mongox.Index("name", unique=True),
            mongox.Index(keys=[("year", mongox.Order.DESCENDING), ("genre", mongox.IndexType.HASHED)]),
        ]
```

As you can see `Meta` class expects `indexes` to be a list of `Index` objects.

For creating `Index` objects we have two options, for simple cases we can do:

```python
Index(key_name, **kwargs)
```

But to have more control over index definition we can do:

```python
Index(keys=[(key_name, index_order)], **kwargs)
```

And then, you can then create the collection indexes with:

```python
await Movie.create_indexes()
```

Or to drop the indexes:

```python
await Movie.drop_indexes()
```

Note that this will only drop indexes defined in `Meta` class.
To drop all indexes, even those not defined here you can pass `force=True`:

```python
await Movie.drop_indexes(force=True)
```

And finally if you need to drop a single index by name:

```python
await Movie.drop_index("year_genre)
```

`Index` accepts the following arguments:

* `key` For single key (simple indexes).

* `keys` List of keys and their types.

* `name` Can be specified or automatically generated from keys.

* `background` If the index creation should happen in the background.

* `unique` If the index should be a unique index.

For example:

```python
Index(keys=[("year", Order.DESCENDING)], name="year_index", background=True)
```

To specify order of index you can use `mongox.Order`:

```python
from mongox import Order

Index(keys=[("year", Order.ASCENDING)], name="year_index", background=True)
```

`Order` class has only two attributes `ASCENDING` and `DESCENDING`.

And to specify custom index type, you can pass `mongox.IndexType` instead of index order:

```python
from mongox import IndexType

Index(keys=[("year", IndexType.HASHED)], name="year_index", background=True)
```

`IndexType` has the supported PyMongo index types:

* `GEO2D`

* `GEOSPHERE`

* `HASHED`

* `TEXT`

For a full list of allowed arguments you can refer to the PyMongo docs [here](https://pymongo.readthedocs.io/en/stable/api/pymongo/operations.html#pymongo.operations.IndexModel).

### Embedded Models

Embedded Models are models to be embedded in `mongox.Model`.
The difference is that `EmbeddedModel`s won't be inserted separately
and won't get their seaparate `_id`.

To define Embedded Models you should inherit from `mongox.EmbeddedModel`
and define the fields the same as Pydantic.

```python
import mongox


class Genre(mongox.EmbeddedModel):
    title: str


class Movie(mongox.Model):
    name: str
    genre: Genre
```

and now you can create `Movie` instances with `Genre`:

```python
genre = Genre(title="Action")

await Movie(name="Saving Private Ryan", genre=genre).insert()
```

This will create the following collection:

```json
{"name": "Saving Private Ryan", "genre": {"title": "Action"}}
```

You can then query the movie by embedded model fields:

```python
await Movie.query(Movie.genre.name == "Action").get()
```

Or by using the complete embedded model:

```python
await Movie.query(Movie.genre == genre).get()
```
