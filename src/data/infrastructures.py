from src.data.property import Property

class NodeCapability:
    def __init__(
        self,
        name: str,
        value: Property,
        cost: float = None,
        carb: float = None
    ):
        self.name = name
        self.value = value
        self.cost = cost
        self.carb = carb

class LinkCapability:
    def __init__(
        self,
        name: str,
        value: Property
    ):
        self.name = name
        self.value = value

class Node:
    def __init__(
        self,
        name: str,
        capabilities: set[NodeCapability],
        cost: float = None,
        carb: float = None
    ):
        self.name = name
        self.capabilities = capabilities
        self.cost = cost,
        self.carb = carb

class Link:
    def __init__(self, pair: tuple[Node, Node], capabilities: set[LinkCapability]):
        self.pair = pair
        self.capabilities = capabilities

class Infrastructure:
    def __init__(self, name: str, nodes: set[Node], links: set[Link]):
        self.name = name
        self.nodes = nodes
        self.links = links
