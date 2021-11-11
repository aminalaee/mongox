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

* `sort` to sort documents the same way Motor/PyMongo allows:

```python
movies = await Movie.query().sort([(Movie.name, mongox.Order.DESCENDING)]).all()
```

You can use `Order` from `mongox` to have `ASCENDING` or `DESCENDING` order.

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

movie.name = "Another Movie"
movie = await movie.save()
```

Here the output of `save` will also be a `Movie` instance.

This is the equivalent of a MongoDB `updateOne`.

You can also do bulk updates like this:

```python
movies = await Movie.query({Movie.year: 1970}).update({Movie.year: 1980})
```

Here we do an update to change the `year` of all 1970 movies to 1980.

The returned result is a list of update `Movie` instances.
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
