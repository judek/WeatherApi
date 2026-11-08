import pytest
from pydantic import ValidationError

from models.current_weather import CurrentWeather
from models.location import Location
from models.weather import WeatherResponse


def test_current_weather_maps_provider_fields():

    data = {
        "temperature_2m": 82.5,
        "apparent_temperature": 86.0,
        "relative_humidity_2m": 75,
        "cloud_cover": 40,
        "wind_speed_10m": 12.5,
        "wind_direction_10m": 180,
        "wind_gusts_10m": 18.0,
        "weather_code": 2,
        "is_day": 1
    }

    weather = CurrentWeather.model_validate(data)

    assert weather.temperature == 82.5
    assert weather.feels_like == 86.0
    assert weather.humidity == 75
    assert weather.wind_speed == 12.5


def test_current_weather_rejects_missing_required_field():

    data = {
        "temperature_2m": 82.5
    }

    with pytest.raises(ValidationError):
        CurrentWeather.model_validate(data)


def test_location_model():

    location = Location(
        name="Tampa",
        latitude=27.95,
        longitude=-82.46,
        country="United States",
        admin1="Florida"
    )

    assert location.name == "Tampa"
    assert location.admin1 == "Florida"


def test_location_admin1_is_optional():

    location = Location(
        name="Tampa",
        latitude=27.95,
        longitude=-82.46,
        country="United States"
    )

    assert location.admin1 is None


def test_weather_response_model():

    weather = WeatherResponse(
        zip_code="33602",
        location="Tampa, Florida",
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

    assert weather.zip_code == "33602"
    assert weather.location == "Tampa, Florida"
    assert weather.street is None