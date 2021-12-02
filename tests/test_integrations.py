import asyncio
import os

import pytest
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.testclient import TestClient

from mongox.database import Client
from mongox.models import Model

pytestmark = pytest.mark.asyncio


app = Starlette()
database_uri = os.environ.get("DATABASE_URI", "mongodb://localhost:27017")
client = Client(database_uri, get_event_loop=asyncio.get_running_loop)
db = client.get_database("test_db")


class Movie(Model):
    name: str
    year: int

    class Meta:
        collection = db.get_collection("movies")


@pytest.fixture(scope="module", autouse=True)
async def prepare_database() -> None:
    await Movie.query().delete()


@app.route("/", methods=["POST"])
async def create_movies(request):
    data = await request.json()
    movie = await Movie(**data).insert()
    return Response(movie.json(), media_type="application/json")


@app.route("/", methods=["GET"])
async def get_movies(request):
    movie = await Movie.query().first()
    return Response(movie.json(), media_type="application/json")


async def test_starlette_integration() -> None:
    with TestClient(app) as client:
        response = client.post("/", json={"name": "V for Vendetta", "year": 2005})

        assert response.json()["name"] == "V for Vendetta"
        assert response.json()["year"] == 2005
        assert response.status_code == 200

    with TestClient(app) as client:
        response = client.get("/")

        assert response.json()["name"] == "V for Vendetta"
        assert response.json()["year"] == 2005
        assert response.status_code == 200
