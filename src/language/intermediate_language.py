from functools import reduce
from itertools import chain
from collections import OrderedDict

from src.data.resources import Resource
from src.data.applications import Application
from src.data.infrastructures import Infrastructure

class IntermediateStructure:
    def __init__(
        self,
        app: Application,
        infrastructure: Infrastructure,
        flavour_order_strategy: str
    ) -> None:
        self.max_bound = 0

        self.app_name = app.name
        self.cost_budget = app.budget.cost
        self.carbon_budget = app.budget.carbon
        self.components = list()
        self.must_components = list()
        self.flavours = OrderedDict()
        self.importance = OrderedDict()
        self.uses = OrderedDict()
        self.consumable_resource = set()
        self.non_consumable_resource = set()
        self.worst_bounds = OrderedDict()
        self.best_bounds = OrderedDict()
        self.component_requirements = OrderedDict()
        self.dependencies = OrderedDict()
        self.initialize_with_app(app, flavour_order_strategy)

        self.infrastructure_name = infrastructure.name
        self.nodes = list()
        self.node_capabilities = OrderedDict()
        self.node_cost = OrderedDict()
        self.node_carb = OrderedDict()
        self.link_capacity = OrderedDict()
        self.initialize_with_infrastruture(infrastructure)

        # After filling it, make it a list to give it an order
        self.consumable_resource = sorted(list(self.consumable_resource))
        self.non_consumable_resource = sorted(list(self.non_consumable_resource))
        self.resources = self.consumable_resource + self.non_consumable_resource
        self.resources = ["cpu", "ram", "storage", "bwIn", "bwOut", "ssl", "firewall", "encrypted_storage", "availability", "latency"]

    def add_resource(self, r: Resource, resource_name: str = None):
        if resource_name is None:
            resource_name = r.name
        if r.consumable:
            self.consumable_resource.add(resource_name)
        else:
            self.non_consumable_resource.add(resource_name)

        if r.worst_bound is None and r.best_bound is None:
            raise AssertionError(f"At least one of worst_bound or best_bound for resource {resource_name} must have a value")

        if r.worst_bound is not None:
            self.worst_bounds[resource_name] = r.worst_bound
        if r.best_bound is not None:
            self.best_bounds[resource_name] = r.best_bound

    def maybe_update_maxbound(self, value: float):
        if value > self.max_bound:
            self.max_bound = value + 1

    def by_order_strategy(self, components, order_strategy) -> list[set[str]]:
        max_len = max(len(c.flavours) for c in components)
        F_sets = [[] for _ in range(max_len)]

        orders = [c.importance_order for c in components]
        match order_strategy:
            case "min":
                for io in orders:
                    for i, flavour in enumerate(io):
                        if isinstance(flavour, list):
                            for f in flavour:
                                F_sets[i].append(f)
                        else:
                            F_sets[i].append(flavour)
            case "max":
                for io in orders:
                    for i, flavour in zip(range(max_len - len(io), max_len), io):
                        if isinstance(flavour, list):
                            for f in flavour:
                                F_sets[i].append(f)
                        else:
                            F_sets[i].append(flavour)
        return F_sets

    def compute_importance(self, components, order_strategy):
        F_sets = self.by_order_strategy(components, order_strategy)

        # Followng the definition from the model.pdf file
        self.importance = OrderedDict()
        for c, imp_ord_list in {c.name : c.importance_order for c in components}.items():
            for i, flav_name in enumerate(imp_ord_list):
                if isinstance(flav_name, list):
                    for f in flav_name:
                        imp = reduce(lambda x, y: x * y, [
                            len(F) for index, F in enumerate(F_sets)
                            if index < i
                        ], 1)
                        self.importance[(c, f)] = imp + 1 if imp > 1 else 1
                else:
                    imp = reduce(lambda x, y: x * y, [
                        len(F) for index, F in enumerate(F_sets)
                        if index < i
                    ], 1)
                    self.importance[(c, flav_name)] = imp + 1 if imp > 1 else 1

    def initialize_with_app(self, app: Application, order_strategy: str):
        self.compute_importance(app.components, order_strategy)

        for c in app.components:
            self.components.append(c.name)
            if c.must:
                self.must_components.append(c.name)

            flavs = sorted(c.flavours, key=lambda f : self.importance[(c.name, f.name)])
            self.flavours[c.name] = [f.name for f in flavs]
            for f in flavs:
                self.uses[(c.name, f.name)] = {
                    (k, v)
                    for k, v in f.uses
                    if len(f.uses) > 0
                }

                for r in chain(c.requirements, f.requirements):
                    if isinstance(r.value, list):
                        for e in r.value:
                            if e not in r.resource.choices:
                                raise AssertionError(f"Invalid list resource choice \"{r.resource.name}\" in component {c.name}")
                            self.add_resource(r.resource, e)
                            self.component_requirements[(c.name, f.name, e)] = 1
                            self.maybe_update_maxbound(1)
                    else:
                        self.add_resource(r.resource)
                        self.component_requirements[(c.name, f.name, r.resource.name)] = r.value
                        self.maybe_update_maxbound(r.value)

                dependencies = [
                    d
                    for d in app.dependencies
                    if d.source.name == c.name and d.flavour.name == f.name
                ]
                for dep in dependencies:
                    for r in dep.requirements:
                        self.add_resource(r.resource)
                        self.dependencies[
                            (c.name, f.name, dep.target.name, r.resource.name)
                        ] = r.value

        # Fix flavours uses deleting empty ones and give value to the ones that
        # do not specify a flavour
        self.uses = OrderedDict({
            k : ((ct, ft) if ft is not None else (ct, self.flavours[ct][0]))
            for k, v in self.uses.items()
            for ct, ft in v
            if len(v) > 0
        })

    def initialize_with_infrastruture(self, infrastructure: Infrastructure):
        for node in infrastructure.nodes:
            self.nodes.append(node.name)

            for c in node.capabilities:
                if isinstance(c.value, list):
                    for e in c.value:
                        if e not in c.resource.choices:
                            raise AssertionError(f"Invalid list resource choice \"{c.resource.name}\" in node {node.name}")
                        self.add_resource(c.resource, e)
                        self.node_capabilities[(node.name, e)] = 1
                        self.maybe_update_maxbound(1)
                        self.node_cost[(node.name, e)] = c.cost if c.cost is not None else 0
                        self.node_carb[(node.name, e)] = c.carb if c.carb is not None else 0
                else:
                    self.add_resource(c.resource)
                    self.node_capabilities[(node.name, c.resource.name)] = c.value
                    self.maybe_update_maxbound(c.value)
                    self.node_cost[(node.name, c.resource.name)] = c.cost if c.cost is not None else 0
                    self.node_carb[(node.name, c.resource.name)] = c.carb if c.carb is not None else 0

            # If a node cost (or carbon) has all zero values, it means that
            # there was a single carbon value inside the node itself
            node_cost = [
                (c, v)
                for (n, c), v in self.node_cost.items()
                if n == node.name
            ]
            if all([v == 0 for _, v in node_cost]):
                self.node_cost[(node.name, node_cost[0][0])] = node.cost

            node_carb = [
                (c, v)
                for (n, c), v in self.node_carb.items()
                if n == node.name
            ]
            if all([v == 0 for _, v in node_carb]):
                self.node_carb[(node.name, node_carb[0][0])] = node.carb

            self.node_carb = OrderedDict({k : v for k, v in self.node_carb.items() if v != 0})

            # link matrix
            to_nodes = [
                l.pair[1].name
                for l in infrastructure.links
                if l.pair[0].name == node.name
            ]
            for t in to_nodes:
                link_cap = [
                    l.capabilities
                    for l in infrastructure.links
                    if l.pair[0].name == node.name and l.pair[1].name == t
                ]
                for link in link_cap:
                    for c in link:
                        self.add_resource(c.resource)
                        self.link_capacity[(node.name, t, c.resource.name)] = c.value
                        self.link_capacity[(t, node.name, c.resource.name)] = c.value
