import random
import json
import os
from translator.intermediate_language import IntermediateLanguage
from translator.return_enum import ResultEnum

SOLVERS = [ "pulp", "z3",'smt',  "minizinc"]


def check_equal_outputs(outputs: tuple[ResultEnum, list[str] | None]):
    def trim(st):
        # a string like 'a_b_c' should become "a_b"
        st = st.split("_")
        return IntermediateLanguage.flav_to_importance(st[1])

    outputs = list(zip(SOLVERS, outputs))
    outputs = list(
        filter(
            lambda x: x[1][0] == ResultEnum.Sat or\
                  x[1][0] == ResultEnum.NonSat,
            outputs,
        )
    )

    # check if are all non sat
    non_sat = sum(map(lambda x: 1 if x[1][0] == ResultEnum.NonSat else 0, outputs))
    if non_sat != len(outputs) and non_sat != 0:
        return False
    elif non_sat == len(outputs):
        return True

    outputs = list(filter(lambda x: x[0] != "smt", outputs))
    outputs = list(map(lambda x: x[1][1], outputs))
    outputs = list(sum(map(trim, i)) for i in outputs)
    for i in outputs:
        if i != outputs[0]:
            return False
    return True


def benchmark(dir_com, dir_inf):
    from main import get_translator, load_to_intermidiate_language

    os.makedirs("output", exist_ok=True)
    if os.path.isdir(dir_com) and os.path.isdir(dir_inf):
        dir_components = list(
            map(lambda x: os.path.join(dir_com, x), os.listdir(dir_com))
        )
        dir_infrastructure = list(
            map(lambda x: os.path.join(dir_inf, x), os.listdir(dir_inf))
        )
        dir_components.sort()
        dir_infrastructure.sort()
    elif os.path.isfile(dir_com) and os.path.isfile(dir_inf):
        dir_components = [dir_com]
        dir_infrastructure = [dir_inf]
    else:
        raise Exception("Invalid input")

    exceptions = []
    times = []
    outputs = []
    for comp in dir_components:
        for inf in dir_infrastructure:
            current_output = []
            intermediate = load_to_intermidiate_language(comp, inf)
            print("Comp:", len(intermediate.comps), "Inf:", len(intermediate.nodes))
            for output_format in SOLVERS:
                intermediate = load_to_intermidiate_language(comp, inf)
                translator = get_translator(output_format, intermediate)
                out, time = translator.solve()
                print("-----", out, time, output_format)
                current_output.append(out)
                times.append(
                    (
                        output_format,
                        time,
                        len(intermediate.comps),
                        len(intermediate.nodes),
                        out[0]
                    )
                )

            if not check_equal_outputs(current_output):
                exceptions.append((comp, inf, current_output))
            outputs.extend( list(zip(SOLVERS, current_output)))

    # get random 10 digit
    digit = random.randint(1000, 9999)

    with open(f"output/{digit}_benchmark.json", "w") as f:
        f.write(json.dumps(times,cls=CustomEncoder))
    with open(f"output/{digit}_exceptions.json", "w") as f:
        f.write(json.dumps(exceptions,cls=CustomEncoder))
    with open(f"output/{digit}_output.json", "w") as f:
        # translate Result enum to string
        f.write(json.dumps(outputs,cls=CustomEncoder))
    print(exceptions)

# Define a custom JSON encoder
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ResultEnum):
            return str(obj)  # Convert enum to its name
        return super().default(obj)
