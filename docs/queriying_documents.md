Let's say we have defined the following documents:

```python
import mongox


class Movie(mongox.Model):
    name: str
    year: int
```

### Inserting documents

In order to work with documents we'll first need to insert some.

MongoX provides an `insert` method to the document instances.

```python
movie = await Movie(name="Forrest Gump", year=1994).insert()
```

Of course we can also do it in two steps:

```python
movie = Movie(name="Forrest Gump", year=1994)
movie = await movie.insert()
```

This will insert the following document in MongoDB:

```json
{"name": "Forrest Gump", "year": 1994}
```

The great thing about MongoX is that since it's fully type annotated,
you will have great `mypy` and IDE support.

Since `Movie` model is also a `Pydantic` model, you will have autocompletion in your IDE
to know which fields are required.

And you will also know that the result of `insert` will be a `Movie` instance.

<img alt="MongoX insert screenshot" src="https://user-images.githubusercontent.com/19784933/141309006-94785d1b-c0de-4fde-8b7d-f59253657d64.png">


This will lead to more productivity and fewer runtime errors.

Let's say you try to access `genre` of movie:

```python
print(movie.genre)
```

Here `mypy` and your IDE will complain that the `Movie` class has no attribute `genre`.

### Querying documents

MongoX supports the same queries Motor/PyMongo support and besides that,
also introduces two other options.

Let's say you want to query for a single document:

You can do it the usual way, by passing a dictionary of key, values to filter:

```python
movie = await Movie.query({"name": "Forrest Gump"}).get()
```

You can also query by `Movie` class fields:

```python
movie = await Movie.query({Movie.name: "Forrest Gump"}).get()
```

And finally you can use the new query builder (limited yet):

```python
movie = await Movie.query(Movie.name == "Forrest Gump").get()
```

Here you will again have graet IDE and MyPy support,
as they will know the returned type of `get` will be a `Movie`.

<img alt="MongoX insert screenshot" src="https://user-images.githubusercontent.com/19784933/141309006-94785d1b-c0de-4fde-8b7d-f59253657d64.png">

So you can access `movie` attributes safely.

#### Query methods

Here is the list of supported query methods:

* `first` returns the first matching document:

```python
movie = await Movie.query({Movie.name: "Forrest Gump"}).first()
```

* `get` returns the only matching document or throws exceptions:

```python
movie = await Movie.query({Movie.name: "Forrest Gump"}).get()
```

!!! note
    This can raise NoMatchFound or MultipleMatchesFound

* `all` returns all documents matching the criteria:

```python
movies = await Movie.query().all()
```

This will return all matched documents.
It's up to the caller to set the appropriate limits.

* `count` returns count of documents matching the criteria:

```python
count = await Movie.query({Movie.year: 1994}).count()
```

* `sort` to sort documents based on keys:

```python
movies = await Movie.query().sort(Movie.name, mongox.Order.DESCENDING).all()
```

You can also chain multiple `sort` methods:

```python
movies = (
    await Movie.query()
    .sort(Movie.name, Order.DESCENDING)
    .sort(Movie.year, Order.ASCENDING)
    .all()
)
```

Or as a shortcut, you can use the `mongox.Q` class:

```python
movies = await Movie.query().sort(Q.asc(Movie.name)).all()
```

Or chaining multiple sorts again:

```python
movies = (
    await Movie.query()
    .sort(Q.desc(Movie.name))
    .sort(Q.asc(Movie.year))
    .all()
)
```

* `get_or_create` returns the only matching document or creates it with default arguments.

```python
movie = (
    await Movie.query({Movie.name: "Forrest Gump", Movie.year: 1994})
    .get_or_create()
)
```

The method has the ability to receive some other fields to be used for creation when document has not been found.

```python
movie = (
    await Movie.query({Movie.name: "Forrest Gump"})
    .get_or_create({Movie.year: 1994})
)
```

Here the `Movie` will be queried by name `Forrest Gump` and if not found, it will be created with:

```json
{"name": "Forrest Gump", "year": 1994}
```

* `limit` to limit number of documents returned:

```python
movies = await Movie.query().limit(5).all()
```

This will ensure that only 5 documents are returned.

* `skip` number of documents to skip:

```python
movies = await Movie.query().skip(5).all()
```

This will skip the first 5 documents and return the rest.

Sometimes `skip` is used with `limit` together:

```python
movies = await Movie.query().skip(5).limit(5).all()
```

#### Chaining queries

Some of the query methods return results including:

* `all`
* `count`
* `first`
* `get`

These methods will return final results and should only be the last part of the query:

```python
movie = await Movie.query().all()
```

But some of the query methods return queryset again, so you can chain them together:

* `query`
* `sort`
* `skip`
* `limit`

```python
movies = await Movie.query({Movie.name: "Example"}).skip(10).limit(20).all()

movies = await Movie.query({Movie.name: "Example"}).query({Movie.year: 2005}).all()
```

### Updating documents

MongoX provides the same `updateOne` and `updateMany` functions in MongoDB,
but with a different API.

You can update a document by calling `save` on it:

```python
movie = await Movie.query().get()

movie.name = "  "
movie = await movie.save()
```

Here the output of `save` will also be a `Movie` instance.

This is the equivalent of a MongoDB `updateOne`.

You can also do bulk updates like this:

```python
movies = await Movie.query({Movie.year: 1970}).update(year=1980)
```

Here we do an update to change the `year` of all 1970 movies to 1980.

Now let's update multiple fields in a bulk update:

```python
movies = await Movie.query({Movie.name: "Example"}).update(year=1970, name="Another Movie")
```

Here what was done was an update the `year` and `name` of all movies that have the name Example, the year is changed to 1970 and the name to Another Movie.

The both returned results are a list of update `Movie` instances.
This is the equivalent of `updateMany` in MongoDB.

!!! note
    Note how bulk update is called on `Movie` class,
    but single update is called on `Movie` instance.

### Deleting documents

The same as update, MongoX provides MongoDB `deleteOne` and `deleteMany` functions
but with a different API.

In order to delete a single document you should get a document first,
then call `delete` on it:

```python
movie = await Movie.query().get()

await movie.delete()
```

This will remove the movie instance and it is the equivalent of a `deleteOne`.

To delete multiple documents at the same time:

```python
number_of_deleted = await Movie.query({Movie.year: 1980}).delete()
```

This will remove all documents having `year` equal to 1980,
and the returned result is the number of documents deleted.

### Q operator

The `Q` class contains some handy methods for creating queries.

In order to create sort queries you might usually do this:

```python
movies = await Movie.query().sort(Movie.name, Order.DESCENDING).all()
```

But as a short-cut you can use `Q`:

* `Q.asc()` Creates ASCENDING sort.

```python
movies = await Movie.query().sort(Q.asc(Movie.name)).all()
```

* `Q.desc()` Creates DESCENDING sort.

```python
movies = await Movie.query().sort(Q.desc(Movie.name)).all()
```

There are also methods for creating more complex queries:

* `Q.in_()` Querying with `$in` operator.

```python
movies = await Movie.query(Q.in_(Movie.year, [2000, 2001])).all()
```

* `Q.not_in()` Querying with `$nin` operator.

```python
movies = await Movie.query(Q.not_in(Movie.year, [2002, 2003])).all()
```

* `Q.and_()` Creating an `$and` operator.

This will query for movie with name `Forrest Gump` and year `1994`.

They are basically the same:

```python
movie = await Movie.query(Q.and_(Movie.name == "Forrest Gump", Movie.year == 1994)).all()

movie = await Movie.query(Movie.name == "Forrest Gump").query(Movie.year == 1994).all()
```

* `Q.or_()` Creating an `$or` operator.

This will match movies with name `Forrest Gump` or movies with year greater than `2000`.

```python
movies = await Movie.query(Q.or_(Movie.name == "Forrest Gump", Movie.year > 2000)).all()
```

### Embedded Models

Now we change our `Movie` class to include a `Genre`:

```python
import mongox


class Genre(mongox.EmbeddedModel):
    name: str


class Movie(mongox.Model):
    name: str
    genre: Genre
```

then we can create `Movie` instances with `Genre`:

```python
genre = Genre(name="Action")

await Movie(name="Saving Private Ryan", genre=genre).insert()
```

This will create the following document in MongoDB:

```json
{"name": "Saving Private Ryan", "genre": {"name": "Action"}}
```

You can then query the movie by embedded model fields:

```python
await Movie.query(Movie.genre.name == "Action").get()
```

This will be equivalent to the following filter:

```json
{"genre.name": "Action"}
```

Or by using the complete embedded model:

```python
await Movie.query(Movie.genre == genre).get()
```

This will be equivalent to the following filter:

```json
{"genre": {"name": "Action"}}
```
