from typing import List, Literal

ConstraintType = Literal["avoid", "antiaffinity", "affinity"]

class SingleConstraint:
    def __init__(
        self,
        type: ConstraintType,
        energy_oriented: bool = False,
        resilience_oriented: bool = False,
        soft: bool = True
    ):
        self.type = type
        self.energy_oriented = energy_oriented
        self.resilience_oriented = resilience_oriented
        self.soft = soft

class AvoidConstraints(SingleConstraint):
    def __init__(
        self,
        value: str,
        energy_oriented: bool = False,
        resilience_oriented: bool = False,
        soft: bool = True
    ):
        super().__init__("avoid", energy_oriented, resilience_oriented, soft)
        self.value = value

class AffinityConstraints(SingleConstraint):
    def __init__(
        self,
        value: List[str],
        energy_oriented: bool = False,
        resilience_oriented: bool = False,
        soft: bool = True
    ):
        super().__init__("affinity", energy_oriented, resilience_oriented, soft)
        self.component = value[0]
        self.flavour = value[1]

class AntiAffinityConstraints(SingleConstraint):
    def __init__(
        self,
        value: List[str],
        energy_oriented: bool = False,
        resilience_oriented: bool = False,
        soft: bool = True
    ):
        super().__init__("antiaffinity", energy_oriented, resilience_oriented, soft)
        self.component = value[0]
        self.flavour = value[1]

class FlavourConstraints:
    def __init__(
        self,
        name: str,
        constraints: List[SingleConstraint],
    ):
        self.name = name
        self.constraints = constraints

class ComponentConstraints:
    def __init__(
        self,
        name: str,
        flavoured_constraints: List[FlavourConstraints],
    ):
        self.name = name
        self.flavoured_constraints = flavoured_constraints

class Constraints:
    def __init__(self, component_constraints: List[ComponentConstraints]):
        self.component_constraints = component_constraints
