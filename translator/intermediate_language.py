from typing import Any
from pydantic import BaseModel
import itertools

from translator.get_source_nodes import get_roots


class IntermediateLanguage(BaseModel):
    comps: set[str]
    nodes: set[str]
    res: set[str]
    flav: dict[str, set[str]]
    uses: dict[str, dict[str, set[str]]]
    comReq: dict[str, dict[str, dict[str, Any]]]
    depReq: dict[str, dict[str, dict[str, Any]]]
    budget_cost: float
    budget_carbon: float
    nodeCap: dict[str, dict[str, Any]]
    cost: dict[str, dict[str, Any]]
    linkCap: dict[str, dict[str, dict[str, Any]]]

    def flav_to_importance(self, flav):
        if flav == "tiny":
            return 1
        elif flav == "medium":
            return 6
        elif flav == "large":
            return 24
        else:
            return 0

    @property
    def mustComp(self) -> set[str]:
        # split uses by falvor
        flavs = set(itertools.chain.from_iterable(self.uses.values()))
        res = []
        for flav in flavs:
            graph = {comp: self.uses[comp][flav] for comp in self.uses}
            res.append(get_roots(graph))

        # get the roots with less components
        return min(res, key=len)

    @classmethod
    def CRES_LIST(cls):
        return ["cpu", "ram", "storage", "bwIn", "bwOut"]

    @classmethod
    def NRES_LIST(cls):
        return ["latency", "avability", "ssl", "firewall", "encrypted_storage"]

    @classmethod
    def RES_LIST(cls):
        return cls.NRES_LIST() + cls.CRES_LIST()

    def get_link_cap(self, node1, node2):
        if node1 in self.linkCap and node2 in self.linkCap[node1]:
            return self.linkCap[node1][node2]
        elif node2 in self.linkCap and node1 in self.linkCap[node2]:
            return self.linkCap[node2][node1]
        return None

