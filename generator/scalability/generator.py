#!/usr/bin/env python

import argparse
import itertools
import subprocess
from pathlib import Path
import os

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test files.")
    parser.add_argument(
        "-a",
        "--amount",
        type=int,
        help="The number of times to repeat each test",
        default=3
    )
    parser.add_argument(
        "-m",
        "--max",
        type=int,
        help="Max value for the generation of components, nodes, flavours and resources",
        default=3
    )
    args = parser.parse_args()

    processes = []
    generated_top_folder = (Path(__file__).parent.parent / "data").resolve()
    for (cs, fs, ns, rs) in itertools.product(range(1, args.max + 1), repeat=4):
        folder_name = "c" + str(cs) + "_f" + str(fs) + "_n" + str(ns) + "_r" + str(rs)

        processes.append(subprocess.Popen([
            (Path(__file__).parent.parent / "randomizer.py").resolve(),
            str(args.amount),
            "-c", str(cs),
            "-f", str(fs),
            "-n", str(ns),
            "-r", str(rs),
            "-o", (generated_top_folder / folder_name)
        ]))

    [p.wait() for p in processes]

    for folder in os.listdir(generated_top_folder):
        top_folder = Path(generated_top_folder) / folder
        if os.path.isdir(top_folder):
            for e in os.listdir(top_folder):
                e_folder = Path(generated_top_folder) / folder / e
                process = subprocess.run([
                    (Path(__file__).parent.parent.parent / "main.py").resolve(),
                    e_folder / "components.yaml",
                    e_folder / "infrastructure.yaml",
                    "--format=minizinc",
                    "-p", "incremental",
                    "-r", e_folder / "resources.yaml",
                ], stdout=subprocess.PIPE, text=True)

                if process.returncode != 0:
                    continue

                filename = folder + "_" + e + ".dzn"
                with open(e_folder / filename, "w") as f:
                    f.write(process.stdout)
