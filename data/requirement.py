from data.property import Property
from pydantic import BaseModel


class Requirement(BaseModel):
    name: str
    value: Property
    soft: bool


class ComponentRequirement(Requirement):
    general: bool = True


class FlavourRequirement(Requirement):
    flavours_specific: dict[str, str] = {}
    general: bool = False

    def setFlavourSpecific(self, flavour: str, req_name: str):
        self.flavours_specific[flavour] = req_name
