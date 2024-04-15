from typing import Any, Literal
from pydantic import BaseModel

from data.property import Property
from data.requirement import ComponentRequirement, FlavourRequirement

ComponentType = Literal["service", "database", "integration"]


class Component(BaseModel):
    type: ComponentType
    name: str
    type: str
    must: bool = False
    component_requirements: dict[str, ComponentRequirement | FlavourRequirement] = {}
    flavours: dict[str, str] = {}

    def add_flavour(self, flavour, uses):
        self.flavours[flavour] = uses

    def add_component_requirement(self, name: str, value: Property, soft=False):
        self.component_requirements[name] = ComponentRequirement(
            name=name, value=value, soft=soft
        )

    def add_flavour_requirement(self, flavour, req_name, req_value, req_soft=False):
        self.component_requirements[req_name] = FlavourRequirement(
            name=req_name, value=req_value, soft=req_soft
        )
