#!/usr/bin/env python
import argparse

import yaml
from loader import load_application, load_infrastructure, load_resources
from src.data.resources import default_resources
from src.language.intermediate_language import IntermediateStructure
from src.translators.minizinc import MiniZincTranslator

def main(
    components_data,
    infrastructure_data,
    format,
    priority,
    additional_resources_data=None
):
    if additional_resources_data is not None:
        default_resources.update(additional_resources_data)
    resources = load_resources(default_resources)

    infrastructure = load_infrastructure(infrastructure_data, resources)
    app = load_application(components_data, resources)

    intermediate_structure = IntermediateStructure(
        app,
        infrastructure,
        priority
    )

    if format == "minizinc":
        translated = MiniZincTranslator(intermediate_structure)
    else:
        raise Exception("Invalid output format")

    return translated.to_string()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FREEDA YAML complier to solver model")
    parser.add_argument("components", type=str, help="Components YAML file")
    parser.add_argument("infrastructure", type=str, help="Infrastructure YAML file")
    parser.add_argument(
        "--format",
        "-f",
        choices=["minizinc", "smt", "ampl"],
        default="minizinc",
        help="Output format",
    )
    parser.add_argument(
        "--flavour-priority",
        "-p",
        choices=["incremental", "manual", "lexicographic", "reversed"],
        default="incremental",
        help="Flavour order choosing strategy",
    )
    parser.add_argument(
        "--additional-resources",
        "-r",
        metavar="path",
        type=str,
        help="Resources YAML file path"
    )
    args = parser.parse_args()

    with open(args.infrastructure, "r") as yaml_file:
        infrastructure_data = yaml.safe_load(yaml_file)

    with open(args.components, "r") as yaml_file:
        components_data = yaml.safe_load(yaml_file)

    if args.additional_resources is not None:
        with open(args.additional_resources, "r") as yaml_file:
            additional_resources_data = yaml.safe_load(yaml_file)

        result = main(
            components_data,
            infrastructure_data,
            args.format,
            args.flavour_priority,
            additional_resources_data
        )
    else:
        result = main(
            components_data,
            infrastructure_data,
            args.format,
            args.flavour_priority
        )

    print(result)
