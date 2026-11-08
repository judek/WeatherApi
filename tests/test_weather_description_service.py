from models.current_weather import CurrentWeather
from services.weather_description_service import (
    WeatherDescriptionService
)


def create_current_weather(
    weather_code=0,
    temperature=82.0,
    feels_like=85.0,
    humidity=70,
    cloud_cover=20,
    wind_speed=10.0,
    wind_direction=90,
    wind_gusts=15.0
):

    return CurrentWeather(
        temperature=temperature,
        feels_like=feels_like,
        humidity=humidity,
        cloud_cover=cloud_cover,
        wind_speed=wind_speed,
        wind_direction=wind_direction,
        wind_gusts=wind_gusts,
        weather_code=weather_code,
        is_day=1
    )


def test_get_weather_description():

    service = WeatherDescriptionService()

    assert service.get_weather_description(0) == "Clear sky"
    assert service.get_weather_description(2) == "Partly cloudy"
    assert service.get_weather_description(95) == "Thunderstorm"


def test_unknown_weather_code():

    service = WeatherDescriptionService()

    assert (
        service.get_weather_description(999)
        == "Variable weather conditions"
    )


def test_wind_direction():

    service = WeatherDescriptionService()

    assert service.get_wind_direction(0) == "N"
    assert service.get_wind_direction(90) == "E"
    assert service.get_wind_direction(180) == "S"
    assert service.get_wind_direction(270) == "W"
    assert service.get_wind_direction(360) == "N"


def test_generate_description():

    service = WeatherDescriptionService()

    current = create_current_weather()

    daily = {
        "temperature_2m_max": [90.0],
        "temperature_2m_min": [72.0]
    }

    hourly = {
        "precipitation_probability": [10, 20, 30, 15, 10, 5]
    }

    result = service.generate_description(
        current,
        daily,
        hourly
    )

    assert "Clear sky currently" in result
    assert "82°F" in result
    assert "90°F" in result
    assert "72°F" in result
    assert "E at 10 mph" in result
    assert "Rain chances remain relatively low at 30%" in result


def test_generate_description_with_high_rain_probability():

    service = WeatherDescriptionService()

    current = create_current_weather()

    daily = {
        "temperature_2m_max": [90.0],
        "temperature_2m_min": [72.0]
    }

    hourly = {
        "precipitation_probability": [20, 50, 75, 60, 40, 30]
    }

    result = service.generate_description(
        current,
        daily,
        hourly
    )

    assert "75% chance of precipitation" in result


def test_generate_description_with_no_rain_probability():

    service = WeatherDescriptionService()

    current = create_current_weather()

    daily = {
        "temperature_2m_max": [90.0],
        "temperature_2m_min": [72.0]
    }

    hourly = {
        "precipitation_probability": [0, 0, 0, 0, 0, 0]
    }

    result = service.generate_description(
        current,
        daily,
        hourly
    )

    assert "No precipitation is expected" in result