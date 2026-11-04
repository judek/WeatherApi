from models.current_weather import CurrentWeather


class WeatherDescriptionService:

    WEATHER_DESCRIPTIONS = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail"
    }

    def get_weather_description(self, weather_code: int) -> str:
        return self.WEATHER_DESCRIPTIONS.get(
            weather_code,
            "Variable weather conditions"
        )

    def get_wind_direction(self, degrees: int) -> str:
        directions = [
            "N", "NNE", "NE", "ENE",
            "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW",
            "W", "WNW", "NW", "NNW"
        ]

        index = round(degrees / 22.5) % 16
        return directions[index]

    def generate_description(
        self,
        current: CurrentWeather,
        daily: dict,
        hourly: dict
    ) -> str:

        condition = self.get_weather_description(
            current.weather_code
        )

        high = daily["temperature_2m_max"][0]
        low = daily["temperature_2m_min"][0]

        # Look at precipitation probability over the next six hours
        precipitation_values = hourly.get(
            "precipitation_probability", []
        )[:6]

        precipitation_chance = max(
            precipitation_values,
            default=0
        )

        wind_direction = self.get_wind_direction(
            current.wind_direction
        )

        # First sentence: Current conditions and temperatures
        sentence_one = (
            f"{condition} currently, with a temperature of "
            f"{current.temperature:.0f}°F and a feels-like "
            f"temperature of {current.feels_like:.0f}°F. "
            f"Today's high is expected to reach {high:.0f}°F "
            f"with an overnight low of {low:.0f}°F."
        )

        # Second sentence: Wind and precipitation outlook
        sentence_two = (
            f"Humidity is {current.humidity}%, with "
            f"{current.cloud_cover}% cloud cover. "
            f"Winds are from the {wind_direction} at "
            f"{current.wind_speed:.0f} mph, with gusts up to "
            f"{current.wind_gusts:.0f} mph. "
        )

        if precipitation_chance >= 50:
            sentence_two += (
                f"There is a {precipitation_chance}% chance "
                f"of precipitation over the next six hours."
            )
        elif precipitation_chance > 0:
            sentence_two += (
                f"Rain chances remain relatively low at "
                f"{precipitation_chance}% over the next six hours."
            )
        else:
            sentence_two += (
                "No precipitation is expected over the next six hours."
            )

        return f"{sentence_one} {sentence_two}"