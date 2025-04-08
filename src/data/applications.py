from typing import Literal, Any

from src.data.resources import Resource
from src.data.property import Property

ComponentType = Literal["service", "database", "integration"]

class Requirement:
    def __init__(
        self,
        resource: Resource,
        value: Property,
        soft: bool = False
    ):
        self.resource = resource
        self.value = value
        self.soft = soft
    def __str__(self) -> str:
        return str(self.resource.name) + "_" + str(self.value)
    def __repr__(self) -> str:
        return str(self.resource.name) + "_" + str(self.value)

class Flavour:
    def __init__(
        self,
        name: str,
        uses: set[tuple[str, str]],
        energy: int,
        importance: int = None
    ):
        self.name = str(name)
        self.uses = uses
        self.energy = energy
        self.requirements = list()
        self.importance = importance

    def add_requirement(self, requirement: Requirement):
        self.requirements.append(requirement)

class Component:
    def __init__(
        self,
        name: str,
        type: ComponentType,
        flavours: list[Flavour],
        must: bool,
        importance_order: list[Any] # str | list[str] heterogeneously each indicating a name in the flavours list
    ):
        self.name = name
        self.type = type
        self.flavours = flavours
        self.must = must
        self.requirements = list()
        self.importance_order = importance_order

    def add_requirement(self, requirement: Requirement):
        self.requirements.append(requirement)

class Budget:
    def __init__(self, cost: int, carbon: int):
        self.cost = cost
        self.carbon = carbon

class Dependency:
    def __init__(
        self,
        source: Component,
        flavour: Flavour,
        target: Component,
        energy: int,
        requirements: set[Requirement]
    ):
        self.source = source
        self.flavour = flavour
        self.target = target
        self.energy = energy
        self.requirements = requirements

class Application:
    def __init__(
        self,
        name: str,
        components: set[Component],
        dependencies: set[Dependency],
        budget: Budget
    ):
        self.name = name
        self.components = components
        self.dependencies = dependencies
        self.budget = budget
