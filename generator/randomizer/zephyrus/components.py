import random

import networkx as nx

def random_sample(l):
    return random.sample(l, k=random.randint(0, len(l)))

def create_dag(graph, components_name, flavours_names):
    # Construct a directed aciclic graph from the starter one
    dag = nx.DiGraph()
    dag.add_nodes_from(graph.nodes)

    for u, v in graph.edges:
        dag.add_edge(u, v)
        if not nx.is_directed_acyclic_graph(dag):
            dag.remove_edge(u, v)

    # Create uses - initialize
    uses = {}
    for c in components_name:
        for f in flavours_names[components_name.index(c)]:
            uses[(c, f)] = list()

    # Create uses - fill with starter graph
    for u, v in dag.edges:
        u_component = "component_" + str(u)
        v_component = "component_" + str(v)

        u_index = components_name.index(u_component)
        u_flavours = flavours_names[u_index]
        for f in random.sample(u_flavours, k=random.randint(1, len(u_flavours))):
            if bool(random.getrandbits(1)):
                v_index = components_name.index(v_component)
                v_selected_flavour = random.choice(flavours_names[v_index])

                uses[(u_component, f)].append({
                    "component" : v_component,
                    "min_flavour" : v_selected_flavour
                })
            else:
                uses[(u_component, f)].append(v_component)

    return uses

def generate_topology(starter_graph, components_amount, flavours_amount, amount):
    components_name = ["component_" + str(c) for c in range(components_amount)]
    flavours_amount = [
        random.choice([1, random.randint(2, flavours_amount)])
        for _ in components_name
    ]
    flavours_names = [
        ["flavour_" + str(i) for i in range(f)]
        for f in flavours_amount
    ]

    uses_names = create_dag(starter_graph, components_name, flavours_names)

    components_dict = {}
    for i_c, c_name in enumerate(components_name):
        flavours = {}
        for f_name in flavours_names[i_c]:
            flavours[f_name] = {"uses" : uses_names[(c_name, f_name)]}

        component_dict = {
            "type" : "service",
            "must" : True,
            "flavours" : flavours,
            "importance_order" : [flavours_names[i_c]]
        }

        components_dict[c_name] = component_dict

    return components_name, flavours_names, components_dict

def generate_flavours_resources_dependencies(
    components_name,
    flavours_names,
    resources,
    requirements_scaling_factor
):
    result = {}

    cons_res_names = [n for n, _ in resources.items()] # Zephyrus: has only consumable resources
    for i_c, c in enumerate(components_name):
        resources_names_common = random.sample(
            cons_res_names,
            k=random.randint(
                0,
                len(cons_res_names) - 1 if len(cons_res_names) else 0
            )
        )
        result[c] = {}
        if len(resources_names_common) > 0:
            for r_name in resources_names_common:
                r = [r for n, r in resources.items() if n == r_name][0]
                value = (
                    random.randint(
                        r["worst_bound"] / requirements_scaling_factor,
                        r["best_bound"] / requirements_scaling_factor
                    ) if r["optimization"] == "maximization"
                    else random.randint(
                        r["best_bound"] / requirements_scaling_factor,
                        r["worst_bound"] / requirements_scaling_factor
                    )
                )
            result[c]["common"] = {
                r_name : {
                    "value" : value,
                    "soft" : bool(random.getrandbits(1))
                }
            }
        else:
            result[c]["common"] = {}

        old_values = {}
        result[c]["flavour-specific"] = {}
        resources_names_flavour = [r for r in resources.keys() if r not in resources_names_common]
        for f in flavours_names[i_c]:
            for r_name in resources_names_flavour:
                r = [r for n, r in resources.items() if n == r_name][0]
                if r_name not in old_values:
                    value = (
                        random.randint(
                            int(r["worst_bound"] / requirements_scaling_factor),
                            int(r["best_bound"] / requirements_scaling_factor)
                        ) if r["optimization"] == "maximization"
                        else random.randint(
                            int(r["best_bound"] / requirements_scaling_factor),
                            int(r["worst_bound"] / requirements_scaling_factor)
                        )
                    )
                    old_values[r_name] = value
                else:
                    value = (
                        random.randint(
                            old_values[r_name],
                            int(r["best_bound"] / requirements_scaling_factor)
                        ) if r["optimization"] == "maximization"
                        else random.randint(
                            int(r["best_bound"] / requirements_scaling_factor),
                            old_values[r_name]
                        )
                    )
                old_values[r_name] = value
                result[c]["flavour-specific"][f] = {
                    r_name : {
                        "value" : value,
                        "soft" : bool(random.getrandbits(1))
                    }
                }

    return result

def generate_app_as_in_zephyrus(
    resources,
    components_amount,
    flavours_amount,
    amount,
    starting_components_topology,
    requirements_scaling_factor
):
    application = {
        "name" : "app",
        "components" : {},
        "requirements" : {
            "components" : {},
            "dependencies" : {},
            "budget": {
                "cost": 2_000_000, #random.randint(0, 1_000_000),
                "carbon": 2_000_000 # Zephyrus: it does not have carb, but we keep the budget high
            }
        }
    }

    components_name, flavours_names, components_dict = generate_topology(
        starting_components_topology,
        components_amount,
        flavours_amount,
        amount
    )
    application["components"] = components_dict

    application["requirements"]["components"] = generate_flavours_resources_dependencies(
        components_name,
        flavours_names,
        resources,
        requirements_scaling_factor
    )

    return application