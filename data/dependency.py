from data.property import Property
from data.requirement import Requirement
from pydantic import BaseModel


class Dependency(BaseModel):
    source: str
    flavour: str
    target: str
    requirements: dict[str, Requirement] = {}

    def add_requirement(self, name: str, value: Property, soft=False):
        self.requirements[name] = Requirement(name=name, value=value, soft=soft)
