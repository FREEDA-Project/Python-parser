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

def get_resource(resources: list[Resource], r_name: Resource):
    resource = [r for r in resources if r_name == r.name]
    if len(resource) > 0:
        return resource[0]
    else:
        raise AssertionError(f"Unable to find resource \"{r_name}\". Terminating")

def create_components(data, resources: list[Resource]) -> set[Component]:
    # Create components
    components = set()
    for component_name, component_data in data["components"].items():
        type = component_data["type"]
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
                }
                flavours.append(Flavour(f_name, uses))

        # Re-order flavour based on (specified) importance
        if "importance_order" in component_data:
            order = set()
            for f in component_data["importance_order"]:
                if isinstance(f, list):
                    order = order.union(f)
                else:
                    order.add(f)

                importance_order = component_data["importance_order"]
        else:
            importance_order = sorted([f.name for f in flavours])

        # Check: is there a flavour that is not ordered?
        if order.union({f.name for f in flavours}) != order:
            raise NameError(f"Flavours in {component_name} are not completely ordered")

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
            component.add_requirement(Requirement(
                resource,
                req_data["value"],
                req_data.get("soft", False)
            ))

        if "flavour-specific" in req_comp_data:
            for req_flav_name, req_flavs_data in req_comp_data["flavour-specific"].items():
                for req_name, req_data in req_flavs_data.items():
                    resource = get_resource(resources, req_name)
                    flavour_of_component = [
                        f
                        for c in components
                        for f in c.flavours
                        if c.name == c_name and f.name == req_flav_name
                    ][0]
                    flavour_of_component.add_requirement(Requirement(
                        resource,
                        req_data["value"],
                        req_data.get("soft", False)
                    ))

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
                for req_name, req_data in flav_requirements.items():
                    resource = get_resource(resources, req_name)
                    requirements.add(Requirement(
                        resource,
                        req_data["value"],
                        req_data.get("soft", False)
                    ))

                dependencies.add(Dependency(
                    from_component,
                    from_flav,
                    to_component,
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
            carb = None
            if (
                (not isinstance(node_data["profile"]["cost"], (int, float)))
                and
                (c_name in node_data["profile"]["cost"])
            ):
                cost = node_data["profile"]["cost"][c_name]
            if (
                (not isinstance(node_data["profile"]["carbon"], (int, float)))
                and
                (c_name in node_data["profile"]["carbon"])
            ):
                carb = node_data["profile"]["carbon"][c_name]

            resource = get_resource(resources, c_name)
            capabilities.add(NodeCapability(resource, c_value, cost, carb))

        profile_cost = node_data["profile"].get("cost")
        profile_carbon = node_data["profile"].get("carbon")

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
        minimization = True if r_data["optimization"] == "minimization" else False
        consumable = True if "type" in r_data and r_data["type"] == "consumable" else False
        worst_bound = r_data.get("worst_bound")
        best_bound = r_data.get("best_bound")
        if worst_bound is None and best_bound is None:
            raise AssertionError(f"At least one of best_bound and worst_bound must have a value for resource {r_name}")

        if "choices" in r_data:
            resources.append(ListResource(
                r_name,
                minimization,
                r_data["choices"]
            ))
        else:
            resources.append(Resource(
                r_name,
                consumable,
                minimization,
                best_bound,
                worst_bound
            ))
    return resources
