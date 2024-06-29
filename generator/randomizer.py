import argparse
import random
import yaml
import itertools

MAX_RESOURCE_VALUE = 1_000

parser = argparse.ArgumentParser(description="Generate test files.")
parser.add_argument("amount", type=int, help="The number of files to generate")
parser.add_argument("-o", "--output", type=str, help="Output file")
parser.add_argument("-c", "--components", type=int, help="Number of components to generate", default=3)
parser.add_argument("-f", "--flavours", type=int, help="Max number of flavours to generate for each components", default=3)
parser.add_argument("-n", "--nodes", type=int, help="Number of nodes to generate", default=3)
parser.add_argument("-r", "--resources", type=int, help="Number of resources to generate", default=8)
args = parser.parse_args()

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
        match kind[0]:
            case "non-consumable":
                bounds = (
                    random.randint(MAX_RESOURCE_VALUE / 4, MAX_RESOURCE_VALUE / 2),
                    random.randint(MAX_RESOURCE_VALUE / 2, MAX_RESOURCE_VALUE),
                )
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
            case "consumable":
                bounds = (
                    random.randint(MAX_RESOURCE_VALUE / 4, MAX_RESOURCE_VALUE / 2),
                    random.randint(MAX_RESOURCE_VALUE / 2, MAX_RESOURCE_VALUE),
                )
                r.update({
                    "type" : "non-consumable",
                    "optimization" : "minimization",
                    "best_bound" : bounds[0],
                    "worst_bound" : bounds[1]
                })
            case "list":
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
        "requirements" : {},
        "dependencies" : {}
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
        application["requirements"][c] = {}
        for r_name in resources_names_common:
            r = [r for n, r in resources.items() if n == r_name][0]
            if "choices" in r:
                value = random_sample(r["choices"])
            else:
                value = (
                    random.randint(r["worst_bound"], r["best_bound"])
                    if r["optimization"] == "maximization"
                    else random.randint(r["best_bound"], r["worst_bound"])
                )
            application["requirements"][c]["common"] = {
                r_name : {
                    "value" : value,
                    "soft" : bool(random.getrandbits(1))
                }
            }

        old_values = {}
        application["requirements"][c]["flavour-specific"] = {}
        resources_names_flavour = [r for r in resources.keys() if r not in resources_names_common]
        for f in flavours_names[i_c]:
            for r_name in resources_names_flavour:
                r = [r for n, r in resources.items() if n == r_name][0]
                if "choices" in r:
                    value = random_sample(r["choices"])
                else:
                    if r_name not in old_values:
                        value = (
                            random.randint(r["worst_bound"], r["best_bound"])
                            if r["optimization"] == "maximization"
                            else random.randint(r["best_bound"], r["worst_bound"])
                        )
                        old_values[r_name] = value
                    else:
                        value = (
                            random.randint(old_values[r_name], r["best_bound"])
                            if r["optimization"] == "maximization"
                            else random.randint(r["best_bound"], old_values[r_name])
                        )
                    old_values[r_name] = value
                application["requirements"][c]["flavour-specific"][f] = {
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

            application["dependencies"][c] = {}
            application["dependencies"][c][f] = {}
            application["dependencies"][c][f][u_name] = {}
            old_value = {}
            for r in resources_names_dep:
                if (f, u_name, r) in old_value:
                    res = [r for n, r in resources.items() if n == r][0]
                    value = (
                        random.randint(old_values[(f, u_name, r)], res["best_bound"])
                        if res["optimization"] == "maximization"
                        else random.randint(res["best_bound"], old_values[(f, u, r)])
                    )
                    old_values[(f, u_name, r)] = value
                else:
                    res = [res for n, res in resources.items() if n == r][0]
                    value = (
                        random.randint(res["worst_bound"], res["best_bound"])
                        if res["optimization"] == "maximization"
                        else random.randint(res["best_bound"], res["worst_bound"])
                    )
                    old_values[(f, u_name, r)] = value
                application["dependencies"][c][f][u_name][r] = {"value" : value}

    return application

def generate_infrastructure(resources, nodes_amount):
    infrastructure = {
        "name" : "infrastructure",
        "nodes" : {},
        "links" : list()
    }
    nodes_name = ["node_" + str(i) for i in range(nodes_amount)]
    cons_res = [(n, r) for n, r in resources.items() if "type" not in r or r["type"] == "consumable"]
    for name in nodes_name:
        cost = {name : random.randint(0, 100) for name, _ in cons_res}
        carbon = {name : random.randint(0, 100) for name, _ in cons_res}
        capabilities = {}
        for name, resource in cons_res:
            if "choices" in resource:
                capabilities[name] = resource["choices"]
            else:
                max_bound = max(resource["worst_bound"] * 10, resource["best_bound"] * 10)
                min_bound = min(resource["worst_bound"] * 10, resource["best_bound"] * 10)
                capabilities[name] = random.randint(max_bound, min_bound)
        infrastructure["nodes"][name] = {
            "capabilities" : capabilities,
            "cost" : cost,
            "carbon" : carbon
        }
    non_cons_res = [(n, r) for n, r in resources.items() if "type" in r and r["type"] == "non-consumable"]
    for from_node, to_node in itertools.product(nodes_name, nodes_name):
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

for i in range(args.amount):
    resources = generate_resources(args.resources)
    app = generate_app(resources, args.components, args.flavours)
    infrastructure = generate_infrastructure(resources, args.nodes)
    # Nodes
    nodes_name = ["node_" + str(n) for n in range(args.nodes)]

    print(yaml.dump(resources))
