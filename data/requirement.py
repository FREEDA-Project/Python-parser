from data.property import Property
from pydantic import BaseModel


class Requirement(BaseModel):
    name: str
    value: Property
    soft: bool
