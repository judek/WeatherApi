from pydantic import BaseModel


class Location(BaseModel):
    name: str
    latitude: float
    longitude: float
    country: str
    admin1: str | None = None