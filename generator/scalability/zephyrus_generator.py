#!/usr/bin/env python

import argparse
from pathlib import Path
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../randomizer/zephyrus/"))
import randomizer

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
import main_zephyrus

def single_randomizer_generator(raw_args=None):
    parser = argparse.ArgumentParser(description="Generate test files.")
    parser.add_argument("amount", type=int, help="The number of files to generate")
    parser.add_argument("-o", "--output", type=str, help="Location to output file", default=None)
    parser.add_argument("-c", "--components", type=int, help="Number of components to generate", default=3)
    parser.add_argument("-n", "--nodes", type=int, help="Number of nodes to generate", default=3)
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
    args = parser.parse_args(raw_args)

    instance_name = f"c{args.components}_f1" +\
        f"_n{args.nodes}_r1" +\
        f"_g{args.components_graph.split('_')[0]}" +\
        f"_i{args.infrastructure_graph.split('_')[0]}"

    try:
        results = randomizer.randomize(
            args.amount,
            args.components,
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

    freeda_dzns = []
    zephyrus_dzns = []
    for r in results:
        try:
            freeda_dzn, zephyrus_dzn = main_zephyrus.main(
                components_data = r["components"],
                infrastructure_data = r["infrastructure"],
                priority = "lexycographic",
                additional_resources_data = r["resources"]
            )
            freeda_dzns.append(freeda_dzn)
            zephyrus_dzns.append(zephyrus_dzn)
        except Exception as e:
            print(
                "Unable to generate any of",
                instance_name,
                "the following exception occured: \n"
            )
            raise e

    for translated_name, dzns in zip(["freeda", "zephyrus"], [freeda_dzns, zephyrus_dzns]):
        top_folder = Path(args.output) / translated_name
        if args.output is None:
            top_folder = (Path(__file__).parent.parent / "data" / translated_name).resolve()

        for i, dzn in enumerate(dzns):
            filename = f"{instance_name}_{i}.dzn"
            with open(top_folder / filename, "w") as f:
                f.write(dzn)

if __name__ == "__main__":
    single_randomizer_generator()
