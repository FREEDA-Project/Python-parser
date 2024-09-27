import random

def generate_infrastructure(resources, nodes_amount, graph):
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