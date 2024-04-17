from data.property import Property
from pydantic import BaseModel


class Capability(BaseModel):
    name: str
