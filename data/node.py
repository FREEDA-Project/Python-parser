from data.capability import Capability
from pydantic import BaseModel


class Profile(BaseModel):
    cost_ram: float
    cost_cpu: float
    cost_storage: float
    carbon: float


class Node(BaseModel):
    name: str
    capabilities: dict[str, Capability] = {}
    profile: Profile = {}

    def add_capability(self, name, value):
        self.capabilities[name] = Capability(name=name, value=value)

    def set_profile(self, cost_ram, cost_cpu, cost_storage, carbon):
        self.profile = Profile(
            cost_ram=cost_ram,
            cost_cpu=cost_cpu,
            cost_storage=cost_storage,
            carbon=carbon,
        )
