#!/usr/bin/env python

import argparse
import random
import yaml
import os
import functools
from pathlib import Path

import networkx as nx

MAX_RESOURCE_VALUE = 1_000
REQUIREMENTS_SCALING_FACTOR = 100

def random_sample(l):
    return random.sample(l, k=random.randint(0, len(l)))

def create_dag(components, flavours):
    uses = {}
    for i, c in enumerate(components):
        for f in flavours[i]:
            uses_comps = random.sample(components[i+1:], k=random.randint(0, len(components[i+1:])))
            uses[(c, f)] = list()
            for u in uses_comps:
                if bool(random.getrandbits(1)):
                    u_index = components.index(u)
                    selected_flavour = random.choice(flavours[u_index])
                    uses[(c, f)].append({
                        "component" : components[u_index],
                        "min_flavour" : selected_flavour
                    })
                else:
                    uses[(c, f)].append(u)
    return uses

def generate_resources(amount):
    resources = {}
    for i in range(amount):
        name = "resource_" + str(i)

        kind = random.choices(
            ["consumable", "non-consumable", "list"],
            k=1,
            weights=[0.5, 0.25, 0.25]
        )
        r = {}
        bounds = (
            random.randint(0, MAX_RESOURCE_VALUE / 10),
            random.randint(MAX_RESOURCE_VALUE - (MAX_RESOURCE_VALUE / 10), MAX_RESOURCE_VALUE),
        )
        if kind[0] == "non-consumable":
            if bool(random.getrandbits(1)):
                optimization = "maximization"
                bound_dict = {"best_bound" : bounds[1], "worst_bound" : bounds[0]}
            else:
                optimization = "minimization"
                bound_dict = {"best_bound" : bounds[0], "worst_bound" : bounds[1]}
            r.update({
                "type" : "non-consumable",
                "optimization" : optimization
            })
            r.update(bound_dict)
        elif kind[0] == "consumable":
            r.update({
                "type" : "non-consumable",
                "optimization" : "minimization",
                "best_bound" : bounds[0],
                "worst_bound" : bounds[1]
            })
        elif kind[0] == "list":
            if bool(random.getrandbits(1)):
                optimization = "maximization"
                bound = {"best_bound" : 1, "worst_bound" : 0}
            else:
                optimization = "minimization"
                bound = {"best_bound" : 0, "worst_bound" : 1}
            r.update({
                "choices" : [
                    name + "_" + str(i)
                    for i in range(random.randint(0, amount))
                ],
                "optimization" : optimization,
            })
            r.update(bound)

        resources[name] = r

    return resources

def generate_app(resources, components_amount, flavours_amount):
    application = {
        "name" : "app",
        "components" : {},
        "requirements" : {
            "components" : {},
            "dependencies" : {},
            "budget": {
                "cost": 2_000_000, #random.randint(0, 1_000_000),
                "carbon": 2_000_000 #random.randint(0, 10)
            }
        }
    }

    components_name = ["component_" + str(c) for c in range(components_amount)]
    flavours_amount = [
        random.choice([1, random.randint(2, flavours_amount)])
        for _ in components_name
    ]
    flavours_names = [
        ["flavour_" + str(i) for i in range(f)]
        for f in flavours_amount
    ]
    uses_names = create_dag(components_name, flavours_names)

    # Components, flavour and uses
    for i_c, c_name in enumerate(components_name):
        flavours = {}
        for f_name in flavours_names[i_c]:
            flavours[f_name] = {"uses" : uses_names[(c_name, f_name)]}

        component_dict = {
            "type" : "service",
            "must" : bool(random.getrandbits(1)), # Either True or False
            "flavours" : flavours,
            "importance_order" : flavours_names[i_c]
        }

        application["components"][c_name] = component_dict

    # Flavour resources dependencies
    cons_res_names = [n for n, r in resources.items() if "type" not in r or r["type"] == "consumable"]
    for i_c, c in enumerate(components_name):
        resources_names_common = random.sample(
            cons_res_names,
            k=random.randint(
                0,
                len(cons_res_names) - 1 if len(cons_res_names) else 0
            )
        )
        application["requirements"]["components"][c] = {}
        if len(resources_names_common) > 0:
            for r_name in resources_names_common:
                r = [r for n, r in resources.items() if n == r_name][0]
                if "choices" in r:
                    value = random_sample(r["choices"])
                else:
                    value = (
                        random.randint(
                            r["worst_bound"] / REQUIREMENTS_SCALING_FACTOR,
                            r["best_bound"] / REQUIREMENTS_SCALING_FACTOR
                        ) if r["optimization"] == "maximization"
                        else random.randint(
                            r["best_bound"] / REQUIREMENTS_SCALING_FACTOR,
                            r["worst_bound"] / REQUIREMENTS_SCALING_FACTOR
                        )
                    )
                application["requirements"]["components"][c]["common"] = {
                    r_name : {
                        "value" : value,
                        "soft" : bool(random.getrandbits(1))
                    }
                }
        else:
            application["requirements"]["components"][c]["common"] = {}

        old_values = {}
        application["requirements"]["components"][c]["flavour-specific"] = {}
        resources_names_flavour = [r for r in resources.keys() if r not in resources_names_common]
        for f in flavours_names[i_c]:
            for r_name in resources_names_flavour:
                r = [r for n, r in resources.items() if n == r_name][0]
                if "choices" in r:
                    value = random_sample(r["choices"])
                else:
                    if r_name not in old_values:
                        value = (
                            random.randint(
                                int(r["worst_bound"] / REQUIREMENTS_SCALING_FACTOR),
                                int(r["best_bound"] / REQUIREMENTS_SCALING_FACTOR)
                            ) if r["optimization"] == "maximization"
                            else random.randint(
                                int(r["best_bound"] / REQUIREMENTS_SCALING_FACTOR),
                                int(r["worst_bound"] / REQUIREMENTS_SCALING_FACTOR)
                            )
                        )
                        old_values[r_name] = value
                    else:
                        value = (
                            random.randint(
                                old_values[r_name],
                                int(r["best_bound"] / REQUIREMENTS_SCALING_FACTOR)
                            ) if r["optimization"] == "maximization"
                            else random.randint(
                                int(r["best_bound"] / REQUIREMENTS_SCALING_FACTOR),
                                old_values[r_name]
                            )
                        )
                    old_values[r_name] = value
                application["requirements"]["components"][c]["flavour-specific"][f] = {
                    r_name : {
                        "value" : value,
                        "soft" : bool(random.getrandbits(1))
                    }
                }

    # Dependencies between components
    non_cons_res_names = [n for n, r in resources.items() if "type" in r and r["type"] == "non-consumable"]
    resources_names_dep = random_sample(non_cons_res_names)
    uses_cleaned = [(c, f, u) for (c, f), u in uses_names.items() if len(u) > 0]
    if len(resources_names_dep) > 0:
        for c, f, u in uses_cleaned:
            u_name = u[0] if isinstance(u[0], str) else u[0]["component"]

            application["requirements"]["dependencies"][c] = {}
            application["requirements"]["dependencies"][c][f] = {}
            application["requirements"]["dependencies"][c][f][u_name] = {}
            old_value = {}
            for r in resources_names_dep:
                if (f, u_name, r) in old_value:
                    res = [r for n, r in resources.items() if n == r][0]
                    value = (
                        random.randint(
                            old_values[(f, u_name, r)],
                            int(res["best_bound"] / REQUIREMENTS_SCALING_FACTOR)
                        ) if res["optimization"] == "maximization"
                        else random.randint(
                            int(res["best_bound"] / REQUIREMENTS_SCALING_FACTOR),
                            old_values[(f, u, r)]
                        )
                    )
                    old_values[(f, u_name, r)] = value
                else:
                    res = [res for n, res in resources.items() if n == r][0]
                    value = (
                        random.randint(
                            int(res["worst_bound"] / REQUIREMENTS_SCALING_FACTOR),
                            int(res["best_bound"] / REQUIREMENTS_SCALING_FACTOR)
                        ) if res["optimization"] == "maximization"
                        else random.randint(
                            int(res["best_bound"] / REQUIREMENTS_SCALING_FACTOR),
                            int(res["worst_bound"] / REQUIREMENTS_SCALING_FACTOR)
                        )
                    )
                    old_values[(f, u_name, r)] = value
                application["requirements"]["dependencies"][c][f][u_name][r] = {"value" : value}

    return application

def generate_infrastructure(resources, nodes_amount, topology_generator_fn):
    node_name_prefix = "node_"

    infrastructure = {
        "name" : "infrastructure",
        "nodes" : {},
        "links" : list()
    }
    nodes_name = [node_name_prefix + str(i) for i in range(nodes_amount)]
    cons_res = [(n, r) for n, r in resources.items() if "type" not in r or r["type"] == "consumable"]
    for name in nodes_name:
        capabilities = {}
        for res_name, resource in cons_res:
            if "choices" in resource:
                capabilities[res_name] = resource["choices"]
            else:
                max_bound = max(resource["worst_bound"] * 1000, resource["best_bound"] * 1000)
                min_bound = min(resource["worst_bound"] * 1000, resource["best_bound"] * 1000)
                capabilities[res_name] = random.randint(max_bound, min_bound)
        infrastructure["nodes"][name] = {
            "capabilities" : capabilities,
            "profile" : {
                "cost" : random.randint(1, 10),
                "carbon" : random.randint(1, 10)
            }
        }
    non_cons_res = [(n, r) for n, r in resources.items() if "type" in r and r["type"] == "non-consumable"]
    graph = topology_generator_fn()
    from_tos = [("node_" + str(ef), "node_" + str(et)) for ef, et in graph.edges()]
    for from_node, to_node in from_tos:
        capabilities = {}
        for name, resource in non_cons_res:
            max_bound = max(resource["worst_bound"], resource["best_bound"])
            min_bound = min(resource["worst_bound"], resource["best_bound"])
            min_bound = min_bound * 2 if min_bound * 2 < max_bound else max_bound
            capabilities[name] = random.randint(min_bound, max_bound)
        infrastructure["links"].append({
            "connected_nodes" : [from_node, to_node],
            "capabilities" : capabilities
        })

    return infrastructure

def randomize(
    amount,
    components,
    flavours,
    res,
    nodes,
    infrastructure_topology_generator_fn
):
    result = []
    for _ in range(amount):
        resources = generate_resources(res)
        app = generate_app(resources, components, flavours)
        infrastructure = generate_infrastructure(
            resources,
            nodes,
            infrastructure_topology_generator_fn
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
            "gnc",
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

    nodes = args.nodes
    infrastructure_topology = getattr(nx, args.infrastructure_graph + "_graph")

    if args.infrastructure_graph == "barabasi_albert":
        infrastructure_topology = functools.partial(
            infrastructure_topology,
            m=random.randint(nodes // 2, args.nodes)
        )
    elif args.infrastructure_graph == "erdos_renyi":
        infrastructure_topology = functools.partial(
            infrastructure_topology,
            p=0.5
        )
    elif args.infrastructure_graph == "star":
        infrastructure_topology = functools.partial(
            infrastructure_topology,
            nodes - 1
        )
    elif args.infrastructure_graph == "ladder":
        infrastructure_topology = functools.partial(
            infrastructure_topology,
            args.nodes // 2
        )
    else:
        infrastructure_topology = functools.partial(
            infrastructure_topology,
            nodes
        )

    z_fill_amount = len(str(args.amount - 1))

    results = randomize(
        amount = args.amount,
        components = args.components,
        flavours = args.flavours,
        res = args.resources,
        nodes = nodes,
        infrastructure_topology_generator_fn = infrastructure_topology
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
