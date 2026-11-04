from typing import Annotated

from fastapi import FastAPI, Path, Depends, HTTPException

from models.weather import WeatherResponse
from services.weather_service import (
    WeatherService,
    LocationNotFoundError,
    WeatherProviderError
)

app = FastAPI(title="Weather API")


def get_weather_service() -> WeatherService:
    return WeatherService()


@app.get("/")
async def root():
    return {"message": "Weather API is running"}


@app.get("/weather/{zip_code}", response_model=WeatherResponse)
async def get_weather(
    zip_code: Annotated[
        str,
        Path(pattern=r"^[0-9]{5}$")
    ],
    weather_service: Annotated[
        WeatherService,
        Depends(get_weather_service)
    ]
):
    try:
        return await weather_service.get_weather(zip_code)

    except LocationNotFoundError as ex:
        raise HTTPException(
            status_code=404,
            detail=str(ex)
        )

    except WeatherProviderError as ex:
        raise HTTPException(
            status_code=502,
            detail=str(ex)
        )