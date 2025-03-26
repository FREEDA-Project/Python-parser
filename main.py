#!/usr/bin/env python
import argparse

import yaml
from loader import load_application, load_infrastructure, load_resources, load_constraints, load_old_deployment
from src.data.resources import default_resources
from src.language.intermediate_language import IntermediateStructure
from src.translators.minizinc.dzn import DZNTranslator
from src.translators.minizinc.mzn import MZNSecondPhaseTranslator
from src.translators.minizinc.unroll import MZNUnrollTranslator, MZNUnrollSecondPhaseTranslator
from src.translators.zephyrus import ZephyrusTranslator

def main(
    components_data,
    infrastructure_data,
    format,
    priority,
    additional_resources_data=None,
    constraints=None,
    old_deployment=None
):
    first_deployment = True

    if additional_resources_data is not None:
        default_resources.update(additional_resources_data)
    resources = load_resources(default_resources)

    if constraints is not None:
        constraints = load_constraints(constraints)
        first_deployment = False

    if old_deployment is not None:
        old_deployment = load_old_deployment(old_deployment)
        first_deployment = False

    infrastructure = load_infrastructure(infrastructure_data, resources)
    app = load_application(components_data, resources)

    intermediate_structure = IntermediateStructure(
        app,
        infrastructure,
        priority,
        constraints,
        old_deployment
    )

    if format == "minizinc":
        if first_deployment:
            translated = DZNTranslator(intermediate_structure).translate()
        else:
            translated = MZNSecondPhaseTranslator(intermediate_structure).translate()
    elif format == "mof": # Experimental: expenct bugs in the model
        if first_deployment:
            translated = MZNUnrollTranslator(intermediate_structure).translate()
        else:
            translated = MZNUnrollSecondPhaseTranslator(intermediate_structure).translate()
    elif format == "zephyrus": # Only for the first deployment
        translated = ZephyrusTranslator(intermediate_structure)
    else:
        raise Exception("Invalid output format")

    return translated.to_string()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FREEDA YAML complier to solver model")
    parser.add_argument("components", type=str, help="Components YAML file")
    parser.add_argument("infrastructure", type=str, help="Infrastructure YAML file")
    parser.add_argument(
        "--constraints",
        "-c",
        metavar="constraints",
        type=str,
        help="Constraint YAML file",
    )
    parser.add_argument(
        "--old-deployment",
        "-d",
        metavar="deployment",
        type=str,
        help="Old deployment file as released by the solver",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["minizinc", "mof", "smt", "ampl", "zephyrus"],
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

    additional_resources_data = None
    if args.additional_resources is not None:
        with open(args.additional_resources, "r") as yaml_file:
            additional_resources_data = yaml.safe_load(yaml_file)

    constraints = None
    if args.constraints is not None:
        with open(args.constraints, "r") as yaml_file:
            constraints = yaml.safe_load(yaml_file)

    old_deployment = None
    if args.old_deployment is not None:
        with open(args.old_deployment, "r") as f:
            old_deployment = f.read()

    result = main(
        components_data,
        infrastructure_data,
        args.format,
        args.flavour_priority,
        additional_resources_data,
        constraints,
        old_deployment
    )

    print(result)
