
import asyncio
import time

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

    # Nominatim usage policy:
    # Cache results and make no more than one request per second.
    _geocode_cache = {}
    _geocode_cache_ttl = 86400  # 24 hours
    _geocode_lock = asyncio.Lock()
    _last_geocode_request = 0.0

    def __init__(self):
        self.description_service = WeatherDescriptionService()

    async def get_weather(self, zip_code: str) -> WeatherResponse:

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:

                # Convert ZIP code into geographic coordinates.
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
                location = Location(
                    name="GPS location",
                    latitude=latitude,
                    longitude=longitude,
                    country=""
                )

                # Resolve GPS coordinates into a readable address.
                # Weather lookup continues even if this fails.
                address = await self._reverse_geocode(
                    client,
                    latitude,
                    longitude
                )

                if address:
                    location.name = (
                        address.get("city")
                        or address.get("town")
                        or address.get("village")
                        or address.get("suburb")
                        or address.get("county")
                        or "GPS location"
                    )

                    location.admin1 = address.get("state")

                return await self._get_weather_for_location(
                    client,
                    location,
                    None,
                    address
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

    async def _reverse_geocode(
        self,
        client: httpx.AsyncClient,
        latitude: float,
        longitude: float
    ) -> dict | None:

        # Round coordinates to improve cache hits.
        cache_key = (
            round(latitude, 4),
            round(longitude, 4)
        )

        cached = self._geocode_cache.get(cache_key)

        if cached:
            address, cached_at = cached

            if time.monotonic() - cached_at < self._geocode_cache_ttl:
                return address

        async with self._geocode_lock:

            # Check cache again after waiting for the lock.
            cached = self._geocode_cache.get(cache_key)

            if cached:
                address, cached_at = cached

                if time.monotonic() - cached_at < self._geocode_cache_ttl:
                    return address

            # Nominatim requires a maximum of one request per second.
            elapsed = time.monotonic() - self._last_geocode_request
            delay = 1.0 - elapsed

            if delay > 0:
                await asyncio.sleep(delay)

            try:
                self.__class__._last_geocode_request = time.monotonic()

                response = await client.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "format": "jsonv2",
                        "addressdetails": 1,
                        "zoom": 18
                    },
                    headers={
                        "User-Agent": "WeatherApi/1.0 (personal weather application)"
                    }
                )

                response.raise_for_status()

                data = response.json()
                address = data.get("address", {})

                self._geocode_cache[cache_key] = (
                    address,
                    time.monotonic()
                )

                return address

            except (httpx.HTTPError, ValueError) as ex:
                # Reverse geocoding is optional. Do not prevent
                # the weather forecast from being returned.
                print(f"Reverse geocoding failed: {ex}")
                return None

    async def _get_weather_for_location(
        self,
        client: httpx.AsyncClient,
        location: Location,
        zip_code: str | None,
        address: dict | None = None
    ) -> WeatherResponse:

        # Retrieve current, hourly, and daily weather.
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

            # Geographic coordinates for map links.
            latitude=location.latitude,
            longitude=location.longitude,

            # Reverse-geocoded address details.
            street=(
                address.get("road")
                or address.get("pedestrian")
                if address else None
            ),
            house_number=(
                address.get("house_number") if address else None
            ),
            city=(
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("suburb")
                if address else None
            ),
            county=address.get("county") if address else None,
            state=address.get("state") if address else None,
            postal_code=address.get("postcode") if address else None,
            country=address.get("country") if address else None,

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
