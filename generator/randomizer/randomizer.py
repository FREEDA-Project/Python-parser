#!/usr/bin/env python

import argparse
import random
import yaml
import os
from pathlib import Path

import networkx as nx

from components import generate_app
from infrastructure import generate_infrastructure
from resources import generate_resources

MAX_RESOURCE_VALUE = 1_000
REQUIREMENTS_SCALING_FACTOR = 100

def randomize(
    amount,
    components,
    flavours,
    res,
    nodes,
    starting_components_topology,
    infrastructure_topology
):
    result = []
    for _ in range(amount):
        resources = generate_resources(res, MAX_RESOURCE_VALUE)
        app = generate_app(
            resources,
            components,
            flavours,
            starting_components_topology,
            REQUIREMENTS_SCALING_FACTOR
        )
        infrastructure = generate_infrastructure(
            resources,
            nodes,
            infrastructure_topology
        )

        result.append({
            "resources" : resources,
            "components" : app,
            "infrastructure" : infrastructure
        })

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate test files.")
    parser.add_argument("amount", type=int, help="The number of files to generate")
    parser.add_argument("-o", "--output", type=str, help="Location to output files", default=None)
    parser.add_argument("-c", "--components", type=int, help="Number of components to generate", default=3)
    parser.add_argument("-f", "--flavours", type=int, help="Max number of flavours to generate for each components", default=3)
    parser.add_argument("-r", "--resources", type=int, help="Number of resources to generate", default=8)
    parser.add_argument("-n", "--nodes", type=int, help="Number of nodes to generate", default=3)
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
        default="barabasi_albert"
    )

    args = parser.parse_args()

    # Topology for infrastructure
    nodes = args.nodes
    infrastructure_topology_fn = getattr(nx, args.infrastructure_graph + "_graph")
    if args.infrastructure_graph == "barabasi_albert":
        infrastructure_topology = infrastructure_topology_fn(
            nodes,
            random.randint(nodes // 2, args.nodes)
        )
    elif args.infrastructure_graph == "erdos_renyi":
        infrastructure_topology = infrastructure_topology_fn(nodes, p=0.5)
    elif args.infrastructure_graph == "star":
        infrastructure_topology = infrastructure_topology_fn(nodes - 1)
    elif args.infrastructure_graph == "ladder":
        infrastructure_topology = infrastructure_topology_fn(args.nodes // 2)
    else:
        infrastructure_topology = infrastructure_topology_fn(nodes)

    # Topology for components
    components = args.components
    topology_fn = getattr(nx, args.components_graph + "_graph")
    if args.components_graph == "barabasi_albert":
        starting_components_topology = topology_fn(
            components,
            m=random.randint(components // 2, args.components)
        )
    else:
        starting_components_topology = topology_fn(components, p=0.5, directed=True)

    z_fill_amount = len(str(args.amount - 1))

    results = randomize(
        args.amount,
        args.components,
        args.flavours,
        args.resources,
        nodes,
        starting_components_topology,
        infrastructure_topology
    )

    for i, r in enumerate(results):
        if args.output is None:
            for filename, content in r.items():
                print("############################################")
                print("# " + filename + ".yaml")
                print("############################################")
                print(yaml.dump(content))
                print()
        else:
            generated_path = Path(args.output) / str(i).zfill(z_fill_amount)
            os.makedirs(generated_path, exist_ok=True)

            for filename, content in r.items():
                with open(generated_path / (filename + ".yaml"), "w") as f:
                    yaml.dump(content, f)
