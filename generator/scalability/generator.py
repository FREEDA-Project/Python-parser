#!/usr/bin/env python

import argparse
from pathlib import Path
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
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
    args = parser.parse_args()

    instance_name = f"c{args.components}_f{args.flavours}_n{args.nodes}_r{args.resources}"
    try:
        results = randomizer.randomize(
            args.amount,
            args.components,
            args.flavours,
            args.nodes,
            args.resources
        )
    except Exception as e:
        print(
            "Unable to generate any of",
            instance_name,
            "the following exception occured: \n"
        )
        raise e

    dzns = []
    for r in results:
        try:
            dzns.append(main.main(
                components_data = r["components"],
                infrastructure_data = r["infrastructure"],
                format = "minizinc",
                priority = "incremental",
                additional_resources_data = r["resources"]
            ))
        except Exception as e:
            print(
                "Unable to generate any of",
                instance_name,
                "the following exception occured: \n"
            )
            raise e

    top_folder = Path(args.output)
    if args.output is None:
        top_folder = (Path(__file__).parent.parent / "data").resolve()

    for i, dzn in enumerate(dzns):
        filename = instance_name + f"_{i}.dzn"
        with open(top_folder / filename, "w") as f:
            f.write(dzn)

if __name__ == "__main__":
    single_randomizer_generator()
