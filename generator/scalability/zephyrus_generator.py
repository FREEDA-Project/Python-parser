#!/usr/bin/env python

import argparse
from pathlib import Path
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../randomizer/zephyrus/"))
import randomizer

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import main

def single_randomizer_generator(raw_args=None):
    parser = argparse.ArgumentParser(description="Generate test files.")
    parser.add_argument("amount", type=int, help="The number of files to generate")
    parser.add_argument("-o", "--output", type=str, help="Location to output file", default=None)
    parser.add_argument("-c", "--components", type=int, help="Number of components to generate", default=3)
    parser.add_argument("-f", "--flavours", type=int, help="Max number of flavours to generate for each components", default=3)
    parser.add_argument("-n", "--nodes", type=int, help="Number of nodes to generate", default=3)
    parser.add_argument("-r", "--resources", type=int, help="Number of resources to generate", default=8)
    parser.add_argument(
        "-g",
        "--components-graph",
        type=str,
        help="Graph type for the uses",
        choices=[
            "barabasi_albert",
            "erdos_renyi",
            "gn",
            "ladder",
            "path"
        ],
        default="erdos_renyi"
    )
    parser.add_argument(
        "-i",
        "--infrastructure-graph",
        type=str,
        help="Graph type for the infrastructure",
        choices=[
            "barabasi_albert",
            "erdos_renyi",
            "gn",
            "complete",
            "ladder",
            "cycle",
            "path",
            "star",
            "wheel"
        ],
        default="complete"
    )
    args = parser.parse_args()

    instance_name = f"c{args.components}" +\
        f"_f{args.flavours}" +\
        f"_n{args.nodes}_r1" +\
        f"_g{args.components_graph.split('_')[0]}" +\
        f"_i{args.infrastructure_graph.split('_')[0]}"

    try:
        results = randomizer.randomize(
            args.amount,
            args.components,
            args.flavours,
            args.nodes,
            args.components_graph,
            args.infrastructure_graph
        )
    except Exception as e:
        print(
            "Unable to generate any of",
            instance_name,
            "the following exception occured: \n"
        )
        raise e

    for translator in ["minizinc", "zephyrus"]:
        dzns = []
        translator_instance_name = f"t{translator}_" + instance_name
        for r in results:
            try:
                dzns.append(main.main(
                    components_data = r["components"],
                    infrastructure_data = r["infrastructure"],
                    format = translator,
                    priority = "lexycographic",
                    additional_resources_data = r["resources"]
                ))
            except Exception as e:
                print(
                    "Unable to generate any of",
                    translator_instance_name,
                    "the following exception occured: \n"
                )
                raise e

        top_folder = Path(args.output)
        if args.output is None:
            top_folder = (Path(__file__).parent.parent / "data").resolve()

        for i, dzn in enumerate(dzns):
            filename = translator_instance_name + f"_{i}.dzn"
            with open(top_folder / filename, "w") as f:
                f.write(dzn)

if __name__ == "__main__":
    single_randomizer_generator()
