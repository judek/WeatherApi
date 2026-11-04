
import httpx

from models.weather import WeatherResponse
from models.location import Location
from models.current_weather import CurrentWeather
from services.weather_description_service import WeatherDescriptionService


class LocationNotFoundError(Exception):
    pass


class WeatherProviderError(Exception):
    pass


class WeatherService:

    def __init__(self):
        self.description_service = WeatherDescriptionService()

    async def get_weather(self, zip_code: str) -> WeatherResponse:

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:

                # Convert ZIP code into geographic coordinates
                geocoding_response = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={
                        "name": zip_code,
                        "count": 1,
                        "language": "en",
                        "format": "json"
                    }
                )

                geocoding_response.raise_for_status()

                geocoding_data = geocoding_response.json()
                results = geocoding_data.get("results")

                if not results:
                    raise LocationNotFoundError(
                        f"No location found for ZIP code {zip_code}"
                    )

                location = Location.model_validate(results[0])

                return await self._get_weather_for_location(
                    client,
                    location,
                    zip_code
                )

        except LocationNotFoundError:
            raise

        except httpx.HTTPStatusError as ex:
            raise WeatherProviderError(
                f"Provider HTTP {ex.response.status_code}: "
                f"{ex.response.text}"
            ) from ex

        except httpx.RequestError as ex:
            raise WeatherProviderError(
                f"Unable to connect to weather provider: {ex}"
            ) from ex

    async def get_weather_by_coordinates(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherResponse:

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:

                # GPS already provides the coordinates.
                # No reverse geocoding is required.
                location = Location(
                    name="GPS location",
                    latitude=latitude,
                    longitude=longitude,
                    country=""
                )

                return await self._get_weather_for_location(
                    client,
                    location,
                    None
                )

        except httpx.HTTPStatusError as ex:
            raise WeatherProviderError(
                f"Provider HTTP {ex.response.status_code}: "
                f"{ex.response.text}"
            ) from ex

        except httpx.RequestError as ex:
            raise WeatherProviderError(
                f"Unable to connect to weather provider: {ex}"
            ) from ex

    async def _get_weather_for_location(
        self,
        client: httpx.AsyncClient,
        location: Location,
        zip_code: str | None
    ) -> WeatherResponse:

        # Retrieve current, hourly, and daily weather
        weather_response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location.latitude,
                "longitude": location.longitude,

                "current": (
                    "temperature_2m,"
                    "apparent_temperature,"
                    "relative_humidity_2m,"
                    "cloud_cover,"
                    "wind_speed_10m,"
                    "wind_direction_10m,"
                    "wind_gusts_10m,"
                    "weather_code,"
                    "is_day"
                ),

                "hourly": "precipitation_probability",

                "daily": (
                    "temperature_2m_max,"
                    "temperature_2m_min"
                ),

                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
                "timezone": "auto"
            }
        )

        weather_response.raise_for_status()

        weather_data = weather_response.json()

        current_weather = CurrentWeather.model_validate(
            weather_data["current"]
        )

        daily_data = weather_data["daily"]
        hourly_data = weather_data["hourly"]

        description = self.description_service.generate_description(
            current_weather,
            daily_data,
            hourly_data
        )

        return WeatherResponse(
            zip_code=zip_code or "",
            location=(
                f"{location.name}, {location.admin1}"
                if location.admin1
                else location.name
            ),

            temperature=current_weather.temperature,
            feels_like=current_weather.feels_like,
            humidity=current_weather.humidity,
            cloud_cover=current_weather.cloud_cover,

            wind_speed=current_weather.wind_speed,
            wind_direction=current_weather.wind_direction,
            wind_gusts=current_weather.wind_gusts,

            high_temperature=daily_data["temperature_2m_max"][0],
            low_temperature=daily_data["temperature_2m_min"][0],

            precipitation_probability=max(
                hourly_data["precipitation_probability"][:6],
                default=0
            ),

            weather_code=current_weather.weather_code,
            description=description,
            is_day=current_weather.is_day
        )
