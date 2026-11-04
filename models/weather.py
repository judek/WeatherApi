from pydantic import BaseModel


class WeatherResponse(BaseModel):
    zip_code: str
    location: str

    temperature: float
    feels_like: float
    humidity: int
    cloud_cover: int

    wind_speed: float
    wind_direction: int
    wind_gusts: float

    high_temperature: float
    low_temperature: float
    precipitation_probability: int

    weather_code: int
    description: str
    is_day: int