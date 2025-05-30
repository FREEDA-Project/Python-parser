from typing import Any

from src.data.resources import (
    Resource,
    ListResource
)
from src.data.applications import (
    Flavour,
    Component,
    Dependency,
    Requirement,
    Budget,
    Application
)
from src.data.infrastructures import (
    NodeCapability,
    LinkCapability,
    Node,
    Link,
    Infrastructure
)
from src.data.constraints import(
    AvoidConstraints,
    AffinityConstraints,
    AntiAffinityConstraints,
    FlavourConstraints,
    ComponentConstraints,
    Constraints
)

def get_resource(resources: list[Resource], r_name: Resource):
    resource = [r for r in resources if r_name == r.name]
    if len(resource) > 0:
        return resource[0]
    else:
        raise AssertionError(f"Unable to find resource \"{r_name}\". Terminating")

def add_to_array(array, resource, data):
    if isinstance(data, dict):
        array.add_requirement(Requirement(
            resource,
            data["value"],
            data.get("soft", False)
        ))
    else:
        array.add_requirement(Requirement(
            resource,
            data,
            False
        ))

def create_components(data, resources: list[Resource]) -> set[Component]:
    # Create components
    components = set()
    for component_name, component_data in data["components"].items():
        type = component_data.get("type", "service")
        must = component_data.get("must", False)
        flavours = []

        # Create flavours
        if "flavours" not in component_data:
            flavours.append(Flavour(set(["common"]), 1))
        else:
            for f_name, f_data in component_data["flavours"].items():
                uses = {
                    (u["component"], u["min_flavour"])
                    if isinstance(u, dict) else (u, None)
                    for u in f_data["uses"]
                } if "uses" in f_data else {}
                importance = f_data["importance"] if "importance" in f_data else None
                energy = f_data["energy"]
                flavours.append(Flavour(f_name, uses, energy, importance))

        # Re-order flavour based on (specified) importance
        if "importance_order" in component_data:
            order = set()
            for f in component_data["importance_order"]:
                if isinstance(f, list):
                    order = order.union(f)
                else:
                    order.add(f)

                importance_order = component_data["importance_order"]

            # Check: is there a flavour that is not ordered?
            if order.union({f.name for f in flavours}) != order:
                raise NameError(f"Flavours in {component_name} are not completely ordered")
        else:
            importance_order = sorted([f.name for f in flavours])

        components.add(Component(
            component_name,
            type,
            flavours,
            must,
            importance_order=importance_order
        ))

    # Update requirements
    for c_name, req_comp_data in data["requirements"]["components"].items():
        for req_name, req_data in req_comp_data["common"].items():
            component = [c for c in components if c.name == c_name][0]
            resource = get_resource(resources, req_name)
            add_to_array(component, resource, req_data)

        if "flavour-specific" in req_comp_data:
            for req_flav_name, req_flavs_data in req_comp_data["flavour-specific"].items():
                for req_name, req_data in req_flavs_data.items():
                    flavour_of_component = [
                        f
                        for c in components
                        for f in c.flavours
                        if c.name == c_name and f.name == req_flav_name
                    ][0]
                    resource = get_resource(resources, req_name)
                    add_to_array(flavour_of_component, resource, req_data)

    return components

def create_dependencies(
    data,
    components: set[Component],
    resources: list[Resource]
) -> set[Dependency]:
    dependencies = set()
    for from_name, from_requirements in data["requirements"]["dependencies"].items():
        for flav_name, flav_data in from_requirements.items():
            for to_name, flav_requirements in flav_data.items():
                from_component = [c for c in components if c.name == from_name][0]
                from_flav = [f for f in from_component.flavours if f.name == flav_name][0]
                to_component = [c for c in components if c.name == to_name][0]

                requirements = set()
                for req_name, req_data in flav_requirements["requirements"].items():
                    resource = get_resource(resources, req_name)
                    if isinstance(req_data, dict):
                        requirements.add(Requirement(
                            resource,
                            req_data["value"],
                            req_data.get("soft", False)
                        ))
                    else:
                        requirements.add(Requirement(
                            resource,
                            req_data,
                            False
                        ))

                dependencies.add(Dependency(
                    from_component,
                    from_flav,
                    to_component,
                    flav_requirements["energy"],
                    requirements
                ))
    return dependencies

def create_budget(data) -> Budget:
    return Budget(
        cost=data["requirements"]["budget"]["cost"],
        carbon=data["requirements"]["budget"]["carbon"]
    )

def load_infrastructure(data, resources: list[Resource]) -> Infrastructure:
    nodes = set()
    for node_name in data["nodes"]:
        node_data = data["nodes"][node_name]

        capabilities = set()
        for c_name, c_value in node_data["capabilities"].items():
            cost = None
            if (
                (not isinstance(node_data["profile"]["cost"], (int, float)))
                and
                (c_name in node_data["profile"]["cost"])
            ):
                cost = node_data["profile"]["cost"][c_name]

            resource = get_resource(resources, c_name)
            capabilities.add(NodeCapability(resource, c_value, cost))

        profile_cost = node_data["profile"].get("cost")
        profile_carbon = node_data["profile"].get("carbon", 0)

        nodes.add(Node(node_name, capabilities, profile_cost, profile_carbon))

    links = set()
    for link_data in data["links"]:
        capabilities = set()
        for c_name, c_value in link_data["capabilities"].items():
            resource = get_resource(resources, c_name)
            capabilities.add(LinkCapability(resource, c_value))

        from_node_name, to_node_name = link_data["connected_nodes"]
        try:
            from_node = [n for n in nodes if n.name == from_node_name][0]
        except:
            raise AssertionError(f"Unable to find node with name {from_node_name}")
        try:
            to_node = [n for n in nodes if n.name == to_node_name][0]
        except:
            raise AssertionError(f"Unable to find node with name {to_node}")

        links.add(Link((from_node, to_node), capabilities))

    return Infrastructure(
        data["name"],
        nodes,
        links
    )

def load_application(data: dict[str, Any], resouces: list[Resource]) -> Application:
    components = create_components(data, resouces)
    dependencies = create_dependencies(data, components, resouces)
    budget = create_budget(data)

    app = Application(
        data["name"],
        components,
        dependencies,
        budget
    )

    return app

def load_resources(data: dict[str, Any]) -> list[Resource]:
    resources = []
    for r_name, r_data in data.items():
        worst_bound = r_data.get("worst_bound")
        best_bound = r_data.get("best_bound")
        if worst_bound is None and best_bound is None:
            raise AssertionError(f"At least one of best_bound and worst_bound must have a value for resource {r_name}")

        if "choices" in r_data:
            resources.append(ListResource(
                r_name,
                True,
                r_data["choices"]
            ))
        else:
            resources.append(Resource(
                r_name,
                True if "type" in r_data and r_data["type"] == "consumable" else False,
                True if r_data["optimization"] == "minimization" else False,
                best_bound,
                worst_bound
            ))
    return resources

def load_constraints(data) -> Constraints:
    component_constraints = []
    for comp_name, comp_flavs in data["requirements"]["components"].items():
        constraint_flavours = []
        for flav_name, flav_constraints in comp_flavs.items():
            constraints = []
            for constraint_list in flav_constraints:
                for constraint_name, constraint_values in constraint_list.items():
                    if constraint_name == "avoid":
                        c = AvoidConstraints(
                            constraint_values["value"],
                            constraint_values["energy_oriented"],
                            constraint_values["resilience_oriented"],
                            constraint_values["soft"]
                        )
                    elif constraint_name == "affinity":
                        c = AffinityConstraints(
                            constraint_values["value"],
                            constraint_values["energy_oriented"],
                            constraint_values["resilience_oriented"],
                            constraint_values["soft"]
                        )
                    else: # antiaffinity
                        c = AntiAffinityConstraints(
                            constraint_values["value"],
                            constraint_values["energy_oriented"],
                            constraint_values["resilience_oriented"],
                            constraint_values["soft"]
                        )
                    constraints.append(c)

            constraint_flavours.append(FlavourConstraints(flav_name, constraints))

        component_constraints.append(ComponentConstraints(comp_name, constraint_flavours))

    return Constraints(component_constraints)

def load_old_deployment(data: str) -> dict[str, str]:
    result = {}
    for l in data.split("\n")[:-3]:
        if l.startswith("Component") and not l.endswith("not deployed."):
            words = l.split(" ")
            component = words[1]
            flavour = words[5]
            node = words[8][:-1]

            result.update({(component, flavour) : node})

    return result
