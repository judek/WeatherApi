import pytest

from fastapi.testclient import TestClient

from main import app, get_weather_service
from models.weather import WeatherResponse
from services.weather_service import (
    LocationNotFoundError,
    WeatherProviderError
)


class FakeWeatherService:

    async def get_weather(self, zip_code):

        return create_weather_response(zip_code)

    async def get_weather_by_coordinates(
        self,
        latitude,
        longitude
    ):

        return create_weather_response(
            "",
            location="Tampa, Florida"
        )


class LocationNotFoundService:

    async def get_weather(self, zip_code):
        raise LocationNotFoundError("Location not found")

    async def get_weather_by_coordinates(self, latitude, longitude):
        raise LocationNotFoundError("Location not found")


class WeatherProviderErrorService:

    async def get_weather(self, zip_code):
        raise WeatherProviderError("Weather provider unavailable")

    async def get_weather_by_coordinates(self, latitude, longitude):
        raise WeatherProviderError("Weather provider unavailable")


def create_weather_response(
    zip_code="33602",
    location="Tampa, Florida"
):

    return WeatherResponse(
        zip_code=zip_code,
        location=location,
        temperature=82.5,
        feels_like=86.0,
        humidity=75,
        cloud_cover=40,
        wind_speed=12.5,
        wind_direction=180,
        wind_gusts=18.0,
        high_temperature=89.0,
        low_temperature=72.0,
        precipitation_probability=20,
        weather_code=2,
        description="Partly cloudy",
        is_day=1
    )


@pytest.fixture
def client():

    app.dependency_overrides[get_weather_service] = (
        lambda: FakeWeatherService()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_root_endpoint(client):

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Weather API is running"
    }


def test_get_weather_by_zip(client):

    response = client.get("/api/weather/33602")

    assert response.status_code == 200

    data = response.json()

    assert data["zip_code"] == "33602"
    assert data["location"] == "Tampa, Florida"
    assert data["temperature"] == 82.5


def test_get_weather_by_coordinates(client):

    response = client.get(
        "/api/weather/location",
        params={
            "latitude": 27.95,
            "longitude": -82.46
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["location"] == "Tampa, Florida"
    assert data["temperature"] == 82.5


def test_invalid_zip_code(client):

    response = client.get("/api/weather/123")

    assert response.status_code == 422


def test_invalid_latitude(client):

    response = client.get(
        "/api/weather/location",
        params={
            "latitude": 100,
            "longitude": -82.46
        }
    )

    assert response.status_code == 422


def test_invalid_longitude(client):

    response = client.get(
        "/api/weather/location",
        params={
            "latitude": 27.95,
            "longitude": -200
        }
    )

    assert response.status_code == 422


def test_location_not_found(client):

    app.dependency_overrides[get_weather_service] = (
        lambda: LocationNotFoundService()
    )

    response = client.get("/api/weather/33602")

    assert response.status_code == 404
    assert response.json()["detail"] == "Location not found"


def test_weather_provider_error(client):

    app.dependency_overrides[get_weather_service] = (
        lambda: WeatherProviderErrorService()
    )

    response = client.get("/api/weather/33602")

    assert response.status_code == 502
    assert response.json()["detail"] == "Weather provider unavailable"