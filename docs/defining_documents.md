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
