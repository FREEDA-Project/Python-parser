from typing import Any
from data.application import Application
import itertools

from data.infrastructure import Infrastructure
from data.requirement import Requirement
from data.capability import Capability
from translator.intermediate_language import IntermediateLanguage


class IntermediateLanguageBuilder:
    def __init__(self, app: Application, infrastructure: Infrastructure) -> None:
        self.app = app
        self.infrastructure = infrastructure

    def build(self) -> IntermediateLanguage:
        # Be careful with the order of the following lines
        # cause there are dependencies between them the are
        # not explicit in the code
        self.comps = self._extract_components()
        self.flav = self._extract_flav()
        self.flavs = self._extract_flavours()
        self.uses = self._extract_uses()
        self.nodes = self._extract_nodes()
        self.comReq = self._extract_component_requirements()
        self.depReq = self._extract_dependency_requirements()
        self.linkCap = self._extract_link_cap()
        self.nodeCap = self._extract_node_cap()
        self.cost = self._extract_cost()
        self.res = self._extract_res()
        return IntermediateLanguage(
            comps=self.comps,
            nodes=self.nodes,
            flav=self.flav,
            uses=self.uses,
            budget_carbon=self.app.budget.carbon,
            budget_cost=self.app.budget.cost,
            cost=self.cost,
            comReq=self.comReq,
            depReq=self.depReq,
            linkCap=self.linkCap,
            nodeCap=self.nodeCap,
            res=self.res,
        )

    def _extract_res(self):
        res = set()
        for node in self.comReq.values():
            for flav in node.values():
                for prop in flav.keys():
                    res.add(prop)
        for node in self.depReq.values():
            for flav in node.values():
                for prop in flav.keys():
                    res.add(prop)
        for node in self.nodeCap.values():
            for val in node.keys():
                res.add(val)

        for node in self.linkCap.values():
            for val in node.values():
                for prop in val.keys():
                    res.add(prop)

        return res

    def _extract_proprieties_capability(self, map, prop: Capability | Requirement):
        if isinstance(prop.value, list) and prop.name == "security":
            for flav in IntermediateLanguage.SECURITY_LIST():
                map[flav] = 0
            for flav in prop.value:
                map[flav] = 1
        elif (
            isinstance(prop.value, int) or prop.name in IntermediateLanguage.RES_LIST()
        ):
            map[prop.name] = prop.value
        else:
            raise Exception(
                "Error in the propieties_capability, value must be a float and one of "
                + str(IntermediateLanguage.RES_LIST())
                + "but was given"
                + str(prop)
            )

    def _extract_cost(self):
        cost = {}
        for name, node in self.infrastructure.nodes.items():
            cost[name] = {
                "cpu": int(node.profile.cost_cpu),
                "ram": int(node.profile.cost_ram),
                "storage": int(node.profile.cost_storage),
                "carbon": int(node.profile.carbon),
            }
        return cost

    def _extract_node_cap(self):
        nodeCap = {}
        for node_name, node in self.infrastructure.nodes.items():
            nodeCap[node_name] = {}
            for _, cap in node.capabilities.items():
                self._extract_proprieties_capability(nodeCap[node_name], cap)
        return nodeCap

    def _extract_link_cap(self):
        linkCap = {}
        for link in self.infrastructure.links:
            source, target = link.pair
            if source not in linkCap:
                linkCap[source] = {}
            linkCap[source][target] = {}
            for _, cap in link.capabilities.items():
                self._extract_proprieties_capability(linkCap[source][target], cap)
        return linkCap

    def _extract_nodes(self) -> set[str]:
        return set(self.infrastructure.nodes.keys())

    def _extract_uses(self) -> dict[str, dict[str, set[str]]]:
        uses = {}
        for comp in self.comps:
            for flav in self.flavs:
                if comp not in uses:
                    uses[comp] = {}
                uses[comp][flav] = set(self.app.components[comp].flavours.get(flav, []))
        return uses

    def _extract_components(self) -> set[str]:
        return set(self.app.components.keys())

    def _extract_flav(self) -> dict[str, set[str]]:
        flav = {}
        for comp in self.comps:
            flav[comp] = set(self.app.components[comp].flavours.keys())
        return flav

    def _extract_dependency_requirements(self) -> dict[str, dict[str, dict[str, Any]]]:
        depReq = {}

        for source, deps in self.app.dependencies.items():
            depReq[source] = {}
            for target, dep in deps.items():
                depReq[source][target] = {}
                for req in dep.requirements.values():
                    self._extract_proprieties_capability(depReq[source][target], req)
        return depReq

    def _extract_component_requirements(self):
        comReq = {}

        def _set_requirement(
            component: str, flavours: list[str], requirements: list[Requirement]
        ):
            for flav, req in zip(flavours, requirements):
                if flav not in comReq[component]:
                    comReq[component][flav] = {}
                self._extract_proprieties_capability(comReq[component][flav], req)

        for component in self.app.components.values():
            if len(component.requirements) > 0:
                comReq[component.name] = {}

            for req, req_data in component.requirements.items():
                if isinstance(req_data, list):
                    _set_requirement(
                        component.name,
                        [flavReq.flavour for flavReq in req_data],
                        req_data,
                    )
                else:
                    _set_requirement(
                        component.name,
                        self.flav[component.name],
                        [req_data] * len(self.flav[component.name]),
                    )
        return comReq

    def _extract_flavours(self) -> set[str]:
        return set(
            itertools.chain.from_iterable(
                map(lambda x: x.flavours.keys(), self.app.components.values())
            )
        )
