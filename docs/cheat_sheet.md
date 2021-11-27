All examples are provided for the following collection (without extra boilerplate):

```python
import mongox


class Movie(mongox.Model):
    name: str
    year: int

    class Meta:
        indexes = [mongox.Index("name", unique=True)]
```

### Model methods

`insert`: Inserts the document.

??? example
    ```python
    movie = await Movie(name="Forrest Gump", year=1994).insert()

    movie = Movie(name="Forrest Gump", year=1994)
    await movie.insert()
    ```

`all`: Returns list of all documents matching the query.

??? example
    ```python
    movies = await Movie.query().all()
    ```

`first`: Returns first document matching the query or `None`.

??? example
    ```python
    movie = await Movie.query(Movie.name == "Godfather").first()
    ```

`get`: Returns one document matching the query.

??? example
    ```python
    movie = await Movie.query(Movie.name == "Godfather").get()
    ```

??? warning
    This can throw `NoMatchFound` or `MultipleMatchesFound`.

`count`: Returns count of documents matching the query.

??? example
    ```python
    count = await Movie.query(Movie.year > 2000).count()
    ```

`delete`: Delete a single document or multiple documents.

??? example
    ```python
    # Delete many
    number_of_deleted = await Movie.query(Movie.year < 1950).delete()

    # Delete one
    movie = await Movie.query(Movie.name == "Emma").get()
    await movie.delete()
    ```

`limit`: To limit number of documents returned.

??? example
    ```python
    movies = await Movie.query().limit(5).all()
    ```

`skip`: To skip number of documents for returning results.

??? example
    ```python
    movies = await Movie.query().skip(5).all()

    movies = await Movie.query().skip(5).limit(5).all()
    ```

`sort`: To sort query results.

??? example
    ```python
    from mongox import Order

    movies = await Movie.query().sort(Movie.year, Order.DESC).all()
    ```

`query`: To add another query to query.

??? example
    ```python
    # These queries will have the same result

    movies = await Movie.query(Movie.name > 2000).query(Movie.name < 2020).all()

    movies = await Movie.query(Movie.name > 2000, Movie.name < 2020).all()
    ```

`save`: Saves the document with the current keys and values.

??? example
    ```python
    movie = await Movie(name="Forrest Gump", year=1994).insert()

    movie.year = 2000
    await movie.save()
    ```

### Q operator

`Q.asc()`: Create ascending order expression.

??? example
    ```python
    movies = await Movie.query().sort(Q.asc(Movie.year)).all()
    ```

`Q.desc()`: Create descending order expression.

??? example
    ```python
    movies = await Movie.query().sort(Q.desc(Movie.year)).all()
    ```

`Q.in_()`: Creates an `$in` operator in MongoDB.

??? example
    ```python
    movies = await Movie.query(Q.in_(Movie.year, [2000, 2001])).all()
    ```

`Q.not_in()`: Creates an `$nin` operator in MongoDB.

??? example
    ```python
    movies = await Movie.query(Q.not_in(Movie.year, [1999, 2000])).all()
    ```

`Q.and_()`: Creates an `$and` operator in query.

??? example
    ```python
    movies = await Movie.query(Q.and_(Movie.year > 2000, Movie.year < 2005)).all()
    ```

`Q.or_()`: Creates an `$or` operator in query.

??? example
    ```python
    movies = await Movie.query(Q.or_(Movie.name == "Hobbits", Movie.year > 2000)).all()
    ```

### Indexes

`Model.create_index()`: Creates a single index defined in `Meta` class.

??? example
    ```python
    await Movie.create_index("name")
    ```

??? warning
    This can raise `mongox.InvalidKeyException` if index is not found in `Meta` class.

`Model.create_indexes()`: Creates indexes defined in `Meta` class.

??? example
    ```python
    await Movie.create_indexes()
    ```

??? warning
    This can raise `pymongo.errors.OperationFailure` exception.


`Model.drop_indexes()`: Drops indexes of the collection.

??? example
    ```python
    # Drops indexes defined in Meta class.
    await Movie.drop_indexes()
    ```

??? example
    ```python
    # Drops all indexes of the collection.
    await Movie.drop_indexes(force=True)
    ```

??? warning
    This can raise `pymongo.errors.OperationFailure` exception.

`Model.drop_index()`: Drops a single index by name.

??? example
    ```python
    await Movie.drop_index("name")
    ```

??? warning
    This can raise `mongox.InvalidKeyException` if index is not found in `Meta` class.
