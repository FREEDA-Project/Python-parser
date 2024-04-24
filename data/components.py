from typing import Literal
from pydantic import BaseModel

from data.property import Property
from data.requirement import Requirement, FlavourRequirement

ComponentType = Literal["service", "database", "integration"]


class Component(BaseModel):
    type: ComponentType
    name: str
    type: str
    must: bool = False
    requirements: dict[str, Requirement | list[FlavourRequirement]] = {}
    flavours: dict[str, str] = {}

    def add_flavour(self, flavour, uses):
        self.flavours[flavour] = uses

    def add_component_requirement(self, req_name: str, value: Property, soft=False):
        self.requirements[req_name] = Requirement(name=req_name, value=value, soft=soft)

    def add_flavour_requirement(
        self, flavour: str, req_name, req_value, req_soft=False
    ):
        if req_name not in self.requirements:
            self.requirements[req_name] = []
        else:
            print(req_name)
            print(self.name)
        self.requirements[req_name].append(
            FlavourRequirement(
                name=req_name, value=req_value, soft=req_soft, flavour=flavour
            )
        )
