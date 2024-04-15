from data.budget import Budget
from infrastructure import Capability
from pydantic import BaseModel

class Node(BaseModel):
    name: str
    capabilities: dict[str, Capability] = {}
    profile: Budget = {}
    
    def add_capability(self, name, value):
        self.capabilities[name] = Capability(name, value)
    
    def set_profile(self, cost, carbon):
        self.profile = Budget(cost, carbon)    