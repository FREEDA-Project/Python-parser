from data.budget import Budget
from data.components import Component, ComponentType
from data.dependency import Dependency
from pydantic import BaseModel


class Application(BaseModel):
    name: str
    components: dict[str, Component] = {}
    dependencies: dict[str, Dependency] = {}
    budget: dict[str, Budget] = {}

    def add_component(self, name: str, component_type: ComponentType, must=False):
        self.components[name] = Component(name=name, type=component_type, must=must)

    def add_dependency(self, source: str, flavour: str, target: str):
        self.dependencies[source] = Dependency(source, flavour, target)

    def add_budget(self, cost: float, carbon: float):
        self.budget = Budget(cost=cost, carbon=carbon)
