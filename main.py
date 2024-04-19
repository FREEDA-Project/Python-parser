import yaml
import os
from typing import Any
from data.application import Application
from data.infrastructure import Infrastructure
from intermidiate_language import IntermaediateLanguageBuilder


def _load_components(data: dict[str, Any], app: Application):
    for component_name, component_data in data["components"].items():
        component_type = component_data["type"]
        must = component_data.get("must", False)
        app.add_component(name=component_name, component_type=component_type, must=must)
        # adding flavours
        for flavour, uses in component_data.get("flavours", {}).items():
            app.components[component_name].add_flavour(flavour, uses["uses"])


def _load_requirements(data: dict[str, Any], app: Application):
    # adding requirements to each component
    for component_name, reqs_component_data in data["requirements"]["components"].items():
        # adding general requirements
        for req_name, req_data in reqs_component_data["common"].items():
            req_value = req_data.get("value")
            req_soft = req_data.get("soft", False)
            app.components[component_name].add_component_requirement(
                req_name, req_value, req_soft
            )
        # adding flavour specific requirements
        for flavour_name, flavour_data in reqs_component_data["flavour-specific"].items():
            for req_name, req_data in flavour_data.items():
                req_value = req_data.get("value")
                req_soft = req_data.get("soft", False)
                app.components[component_name].add_flavour_requirement(
                    flavour_name, req_name, req_value, req_soft
                )

    # load dependency
    for from_component, data_extracted in data["requirements"]["dependencies"].items():
        for to_component, requirements in data_extracted.items():
            app.add_dependency(from_component, to_component)
            for req_name, req_data in requirements.items():
                req_value = req_data.get("value")
                req_soft = req_data.get("soft", False)
                app.dependencies[from_component][to_component].add_requirement(
                    req_name, req_value, req_soft
                )

    # load budget
    budget_data = data["requirements"]["budget"]
    cost = budget_data.get("cost")
    carbon = budget_data.get("carbon")
    app.add_budget(cost, carbon)


def load_infrastructure(data: dict[str, Any]) -> Infrastructure:
    infrastructure = Infrastructure(name=data["name"])
    for node_name in data["nodes"]:
        infrastructure.add_node(node_name)
        profile = data["nodes"][node_name].get("profile", {})
        cost_ram = profile["cost"].get("ram", 0)
        cost_cpu = profile["cost"].get("cpu", 0)
        cost_storage = profile["cost"].get("storage", 0)
        carbon = profile.get("carbon", 0)
        infrastructure.nodes[node_name].set_profile(
            cost_ram=cost_ram,
            cost_cpu=cost_cpu,
            cost_storage=cost_storage,
            carbon=carbon,
        )
        for capability_name, capability_value in data["nodes"][node_name]["capabilities"].items():
            infrastructure.nodes[node_name].add_capability(
                capability_name, capability_value
            )

    for link_data in data["links"]:
        connected_nodes = link_data["connected_nodes"]
        infrastructure.add_link(node1=connected_nodes[0], node2=connected_nodes[1])
        for capability_name, capability_value in link_data["capabilities"].items():
            infrastructure.links[-1].add_capability(capability_name, capability_value)
    return infrastructure


def load_application(data: dict[str, Any]) -> Application:
    app = Application(name=data["name"])

    _load_components(data, app)
    _load_requirements(data, app)
    return app


def _diaplay_app(app: Application):
    # Print information to check
    for component_name, component in app.components.items():
        print(f"{component_name}: Type: {component.type}, Must: {component.must}")
        for flavour, uses in component.flavours.items():
            print(f"{flavour}: {uses}")
        print("Component requirements: (common)")
        for req_name, req_data in component.component_requirements.items():
            if req_data.general:
                print(
                    f"{req_name}: {req_data.value}, soft: {req_data.soft}, general requirement: {req_data.general}"
                )
        print("Component requirements: (Flavour-specific)")
        for req_name, req_data in component.component_requirements.items():
            if not (req_data.general):
                print(
                    f"{req_name}: {req_data.value}, soft: {req_data.soft}, general requirement: {req_data.general}"
                )
    return app


if __name__ == "__main__":
    with open("tests/components_example.yaml", "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        app = load_application(data)
        print(app.model_dump_json())
    with open("tests/infrastructure_example.yaml") as yaml_file:
        data = yaml.safe_load(yaml_file)
        infrastructure = load_infrastructure(data)
        print(infrastructure.model_dump_json())
    builder = IntermaediateLanguageBuilder(app)
    print(builder.build()) 
