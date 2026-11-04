from pydantic import BaseModel, Field, ConfigDict


class CurrentWeather(BaseModel):
    temperature: float = Field(validation_alias="temperature_2m")
    feels_like: float = Field(validation_alias="apparent_temperature")
    humidity: int = Field(validation_alias="relative_humidity_2m")
    cloud_cover: int
    wind_speed: float = Field(validation_alias="wind_speed_10m")
    wind_direction: int = Field(validation_alias="wind_direction_10m")
    wind_gusts: float = Field(validation_alias="wind_gusts_10m")
    weather_code: int
    is_day: int

    model_config = ConfigDict(populate_by_name=True)