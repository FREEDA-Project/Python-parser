#!/usr/bin/env python

import argparse
import random
import yaml
import os
from pathlib import Path

import networkx as nx

from components import generate_app_as_in_zephyrus
from infrastructure import generate_infrastructure_as_in_zephyrus

MAX_RESOURCE_VALUE = 1_000
REQUIREMENTS_SCALING_FACTOR = 100

def generate_resources_as_in_zephyrus():
    # Zephyrus has only consumable resources, we will use just one because there
    # is just one cost per node / location in Zephyrus
    return {
        "resource" : {
            "type" : "consumable",
            "optimization" : "minimization",
            "best_bound" : random.randint(0, MAX_RESOURCE_VALUE / 10),
            "worst_bound" : random.randint(MAX_RESOURCE_VALUE - (MAX_RESOURCE_VALUE / 10), MAX_RESOURCE_VALUE)
        }
    }

def convert_string_to_topology(
    components,
    nodes,
    components_graph_str,
    infrastructure_graph_str
):
    # Topology for components
    topology_fn = getattr(nx, components_graph_str + "_graph")
    if components_graph_str == "barabasi_albert":
        starting_components_topology = topology_fn(
            components,
            m=random.randint(components // 2, components - 1)
        )
    elif components_graph_str == "erdos_renyi":
        starting_components_topology = topology_fn(components, p=0.5, directed=True)
    else:
        starting_components_topology = topology_fn(components, create_using=nx.DiGraph)

    # Topology for infrastructure
    infrastructure_topology_fn = getattr(nx, infrastructure_graph_str + "_graph")
    if infrastructure_graph_str == "barabasi_albert":
        infrastructure_topology = infrastructure_topology_fn(
            nodes,
            random.randint(nodes // 2, nodes - 1)
        )
    elif infrastructure_graph_str == "erdos_renyi":
        infrastructure_topology = infrastructure_topology_fn(nodes, p=0.5)
    elif infrastructure_graph_str == "star":
        infrastructure_topology = infrastructure_topology_fn(nodes - 1)
    elif infrastructure_graph_str == "ladder":
        infrastructure_topology = infrastructure_topology_fn(nodes // 2)
    else:
        infrastructure_topology = infrastructure_topology_fn(nodes)

    return starting_components_topology, infrastructure_topology

def randomize(
    amount,
    components,
    flavours,
    nodes,
    starting_components_topology_str,
    infrastructure_topology_str
):
    starting_components_topology, infrastructure_topology = convert_string_to_topology(
        components,
        nodes,
        starting_components_topology_str,
        infrastructure_topology_str
    )

    result = []
    for _ in range(amount):
        resources = generate_resources_as_in_zephyrus()
        app = generate_app_as_in_zephyrus(
            resources,
            components,
            flavours,
            amount,
            starting_components_topology,
            REQUIREMENTS_SCALING_FACTOR
        )
        infrastructure = generate_infrastructure_as_in_zephyrus(
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

    args = parser.parse_args()

    z_fill_amount = len(str(args.amount - 1))

    results = randomize(
        args.amount,
        args.components,
        args.flavours,
        args.nodes,
        args.components_graph,
        args.infrastructure_graph
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
