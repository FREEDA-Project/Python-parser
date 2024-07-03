#!/usr/bin/env python
import argparse

import yaml

from loader import load_application, load_infrastructure, load_resources
from src.language.intermediate_language import IntermediateStructure
from src.translators.minizinc import MiniZincTranslator
#from translators.pulp import PulpTranslator
#from translators.smt import SMTTranslator
#from translators.z3 import Z3Translator

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FREEDA YAML complier to solver model")
    parser.add_argument("components", type=str, help="Components YAML file")
    parser.add_argument("infrastructure", type=str, help="Infrastructure YAML file")
    parser.add_argument("resources", type=str, help="Resources YAML file")
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
        choices=["manual", "lexicographic", "reversed"],
        default="reversed",
        help="Flavour order choosing strategy",
    )
    args = parser.parse_args()

    with open(args.resources, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        resources = load_resources(data)

    with open(args.components, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        app = load_application(data, resources)

    with open(args.infrastructure, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        infrastructure = load_infrastructure(data, resources)

    intermediate_structure = IntermediateStructure(
        app,
        infrastructure,
        args.flavour_priority
    )

    match args.format:
        case "minizinc":
            translated = MiniZincTranslator(intermediate_structure)
    #    case "smt":
    #        translated = SMTTranslator(intermediate_structure)
    #    case "pulp":
    #        translated = PulpTranslator(intermediate_structure)
    #    case "z3":
    #        translated = Z3Translator(intermediate_structure)
    #    case _:
    #        raise Exception("Invalid output format")

    print(translated.to_string())


# TODO:
# - Define a file with the resources
# - Find other todos inside the code