from pydantic import BaseModel
from data.node import Node
from data.capability import Capability

class Link(BaseModel):
    pair: tuple[Node, Node]
    capabilities: dict[str, Capability] = {}
    
    def add_capability(self, name, value):
        self.capabilities[name] = Capability(
            name=name,
            value=value
        )
