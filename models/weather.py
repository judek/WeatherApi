from pydantic import BaseModel


class WeatherResponse(BaseModel):
    zip_code: str
    location: str

    # Geographic coordinates
    latitude: float | None = None
    longitude: float | None = None

    # Reverse-geocoded address details (GPS lookups).
    street: str | None = None
    house_number: str | None = None
    city: str | None = None
    county: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None

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