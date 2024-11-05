import random

def generate_infrastructure_as_in_zephyrus(resources, nodes_amount, graph):
    node_name_prefix = "node_"

    infrastructure = {
        "name" : "infrastructure",
        "nodes" : {},
        "links" : list()
    }
    nodes_name = [node_name_prefix + str(i) for i in range(nodes_amount)]

    for name in nodes_name:
        capabilities = {}
        for res_name, resource in resources.items():
            max_bound = max(resource["worst_bound"] * 1000, resource["best_bound"] * 1000)
            min_bound = min(resource["worst_bound"] * 1000, resource["best_bound"] * 1000)
            capabilities[res_name] = random.randint(min_bound, max_bound)
        infrastructure["nodes"][name] = {
            "capabilities" : capabilities,
            "profile" : {
                "cost" : random.randint(1, 10),
                "carbon" : 1 # Zephyrus: it does not have carb
            }
        }

    from_tos = [("node_" + str(ef), "node_" + str(et)) for ef, et in graph.edges()]
    for from_node, to_node in from_tos:
        infrastructure["links"].append({
            "connected_nodes" : [from_node, to_node],
            "capabilities" : {}
        })

    return infrastructure