
from typing import Annotated
from pathlib import Path as FilePath

from fastapi import FastAPI, Path, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from models.weather import WeatherResponse
from services.weather_service import (
    WeatherService,
    LocationNotFoundError,
    WeatherProviderError
)


app = FastAPI(title="Weather API")


# Dependency injection
def get_weather_service() -> WeatherService:
    return WeatherService()


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
async def root():
    return {"message": "Weather API is running"}


# --------------------------------------------------
# Weather web pages
# --------------------------------------------------

@app.get("/weather", include_in_schema=False)
@app.get("/weather/", include_in_schema=False)
async def weather_page():
    return FileResponse(FilePath("wwwroot/weather.html"))


@app.get("/weather/{zip_code}", include_in_schema=False)
async def weather_page_by_zip(
    zip_code: str
):
    if not zip_code.isdigit() or len(zip_code) != 5:
        raise HTTPException(
            status_code=400,
            detail="Invalid ZIP code"
        )

    return FileResponse(FilePath("wwwroot/weather.html"))


# --------------------------------------------------
# GPS weather API
# --------------------------------------------------

# The first route is used by Windows.
# The second route is available directly through Nginx
# after it removes the /weather prefix.

@app.get(
    "/weather/api/weather/location",
    response_model=WeatherResponse
)
@app.get(
    "/api/weather/location",
    response_model=WeatherResponse
)
async def get_weather_by_coordinates(
    latitude: Annotated[float, Query(ge=-90, le=90)],
    longitude: Annotated[float, Query(ge=-180, le=180)],
    weather_service: Annotated[
        WeatherService,
        Depends(get_weather_service)
    ]
):
    try:
        return await weather_service.get_weather_by_coordinates(
            latitude,
            longitude
        )

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


# --------------------------------------------------
# ZIP-code weather API
# --------------------------------------------------

# Keep this after the GPS endpoint so the literal
# "location" path is not interpreted as a ZIP code.

@app.get(
    "/weather/api/weather/{zip_code}",
    response_model=WeatherResponse
)
@app.get(
    "/api/weather/{zip_code}",
    response_model=WeatherResponse
)
async def get_weather_by_zip(
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
