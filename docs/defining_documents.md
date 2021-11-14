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

Let's say we want to limit the `year` attribute to be more strict:

```python
import mongox


class Movie(mongox.Model):
    name: str
    year: int = mongox.Field(gt=1800)
```

Now you when creating a `Movie` instance, the year will be validated:

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

For a full list of `Field` customizations you can refer to
the Pydantic docs [here](https://pydantic-docs.helpmanual.io/usage/schema/#field-customisation).
