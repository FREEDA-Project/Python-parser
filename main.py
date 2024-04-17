import yaml
import os
from typing import Any
from data.application import Application
from intermidiate_language import IntermaediateLanguageBuilder


def load_app_from_dict(data: dict[str, Any]) -> Application:
    app = Application(name=data["name"])

    for component_name, component_data in data["components"].items():
        component_type = component_data["type"]
        must = component_data.get("must", False)
        app.add_component(name=component_name, component_type=component_type, must=must)
        # adding flavours
        for flavour, uses in component_data.get("flavours", {}).items():
            app.components[component_name].add_flavour(flavour, uses['uses'])

    # adding requirements to each component
    for component_name, reqs_component_data in data["requirements"][
        "components"
    ].items():
        # adding general requirements
        for req_name, req_data in reqs_component_data["common"].items():
            req_value = req_data.get("value")
            req_soft = req_data.get("soft", False)
            component = app.components[component_name]
            component.add_component_requirement(req_name, req_value, req_soft)
        # adding flavour specific requirements
        for flavour_name, flavour_data in reqs_component_data[
            "flavour-specific"
        ].items():
            for req_name, req_data in flavour_data.items():
                req_value = req_data.get("value")
                req_soft = req_data.get("soft", False)
                component = app.components[component_name]
                component.add_flavour_requirement(
                    flavour_name, req_name, req_value, req_soft
                )
    return app


def display_app(app: Application):
    print(app.name)
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




if __name__ == "__main__":
    with open('example.yaml', "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        app = load_app_from_dict(data)
        display_app(app)
        print(app)
        builder = IntermaediateLanguageBuilder(app)
        print(builder.build())