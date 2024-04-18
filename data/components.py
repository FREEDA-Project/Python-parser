from typing import Literal
from pydantic import BaseModel

from data.property import Property
from data.requirement import Requirement

ComponentType = Literal["service", "database", "integration"]


class Component(BaseModel):
    type: ComponentType
    name: str
    type: str
    must: bool = False
    component_requirements: dict[str, Requirement] = {}
    # contain first the flavour and than the requirement name
    flavours_requirements: dict[str, dict[str, Requirement]] = {}
    flavours: dict[str, str] = {}

    def add_flavour(self, flavour, uses):
        self.flavours[flavour] = uses

    def add_component_requirement(self, req_name: str, value: Property, soft=False):
        self.component_requirements[req_name] = Requirement(
            name=req_name, value=value, soft=soft
        )

    def add_flavour_requirement(
        self, flavour: str, req_name, req_value, req_soft=False
    ):
        if flavour not in self.flavours_requirements:
            self.flavours_requirements[flavour] = {}
        self.flavours_requirements[flavour][req_name] = Requirement(
            name=req_name, value=req_value, soft=req_soft
        )
