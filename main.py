import yaml
import json
import os
from banchmark import benchmark
from translator.intermediate_language import IntermediateLanguage
from translator.intermediate_language_builder import IntermediateLanguageBuilder
from translator.translator import Translator
from translator.minizinc import MiniZinc
import argparse
from loader import load_application, load_infrastructure
from translator.return_enum import ResultEnum
import datetime

from tqdm import tqdm
from translator.pulp import PulpTranslator
from translator.smt import SMTTranslator
from translator.z3 import Z3Translator


def load_to_intermidiate_language(app_file, infrastructure_file):
    with open(app_file, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        app = load_application(data)

    with open(infrastructure_file, "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
        infrastructure = load_infrastructure(data)

    builder = IntermediateLanguageBuilder(app, infrastructure)
    intermediate_language = builder.build()

    builder = IntermediateLanguageBuilder(app, infrastructure)
    intermediate_language = builder.build()
    return intermediate_language

def get_translator(name,intermidiate):
    translator_class = None
    match name:
        case "minizinc":
            translator_class = MiniZinc
        case "smt":
            translator_class = SMTTranslator
        case "pulp":
            translator_class = PulpTranslator
        case "z3":
            translator_class = Z3Translator
        case _:
            raise Exception("Invalid output format")
    return translator_class(intermediate_language=intermidiate)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some files.")
    parser.add_argument("components", type=str, help="Components file")
    parser.add_argument("infrastructure", type=str, help="Infrastructure file")
    parser.add_argument("--banchmark",'-b',  help=" compoment and infrastructure should be directory", action='store_true')
    parser.add_argument(
        "--output-format",
        "-f",
        choices=["minizinc", "smt", "pulp", "z3"],
        default="pulp",
        help="Output format",
    )
    parser.add_argument("--output", "-o", type=str, help="file di output")
    # parser -k --key

    args = parser.parse_args()

    if args.banchmark:
        benchmark(args.components, args.infrastructure)
        exit(0)
    else: 
        intermediate = load_to_intermidiate_language(args.components, args.infrastructure)
        translator: Translator = get_translator(args.output_format, intermediate)

        if args.output:
            translator.write_to_file(args.output)
        else:
            print(translator.to_file_string())

