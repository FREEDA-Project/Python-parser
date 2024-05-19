import yaml
import json
import os
from translator.intermediate_language import IntermediateLanguage
from translator.intermediate_language_builder import IntermediateLanguageBuilder
from translator.translator import Translator
from translator.minizinc import MiniZinc
import argparse
from loader import load_application, load_infrastructure
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

def banchmark(dir_com,dir_inf):
    SOLVERS = ["minizinc", "pulp", "z3"]
    os.makedirs("output", exist_ok=True)
    if  os.path.isdir(dir_com) and os.path.isdir(dir_inf):
        dir_components = list(map(lambda x : os.path.join(dir_com,x),os.listdir(dir_com)))
        dir_infrastructure = list(map(lambda x : os.path.join(dir_inf,x),os.listdir(dir_inf)))
    elif os.path.isfile(dir_com) and os.path.isfile(dir_inf):
        dir_components = [dir_com]
        dir_infrastructure = [dir_inf]
    else:
        raise Exception("Invalid input")
    
    def check_equal_outputs(outputs:list[str]|None):
        def trim(st):
            # a string like 'a_b_c' should become "a_b"
            st = st.split("_")
            return IntermediateLanguage.flav_to_importance(st[1])
        
        count_null= sum(map(lambda x: 1 if x is None else 0, outputs))
        if count_null>0 :
            return count_null == len(outputs)
        
        outputs = list(sum(map(trim,i)) for i in outputs)
        # check if all set are equal
        for i in outputs:
            if i != outputs[0]:
                return False
        return True

    exceptions = []
    times = []
    for comp in (dir_components):
        for inf in (dir_infrastructure):
            current_output = []
            intermediate = load_to_intermidiate_language(comp, inf)
            print("Comp:",len(intermediate.comps),"Inf:",len(intermediate.nodes))
            for output_format in SOLVERS:
                translator = get_translator(output_format, intermediate)
                out,time = translator.solve()
                if 5 > time:
                    current_output.append(out)
                print("-----",out,time,output_format)
                times.append((output_format,time,len(intermediate.comps),len(intermediate.nodes)))
                
            if not check_equal_outputs(current_output):
                exceptions.append((comp,inf,current_output))   

    with open("output/benchmark.json", "w") as f:
        f.write(json.dumps(times))
    print(exceptions)



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
        banchmark(args.components, args.infrastructure)
        exit(0)
    else: 
        intermediate = load_to_intermidiate_language(args.components, args.infrastructure)
        translator: Translator = get_translator(args.output_format, intermediate)

        if args.output:
            translator.write_to_file(args.output)
        else:
            print(translator.to_file_string())

