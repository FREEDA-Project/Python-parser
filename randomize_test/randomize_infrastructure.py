import random
from utils import fake, generate_dep, POSSIBILE_REQ_COMP, POSSIBILE_REQ_DEPENDENCY


def generate_infrastructure(nodes_n: int):
    nodes = {}
    for i in range(nodes_n):
        name = "node" + str(i)
        nodes[name] = {}
        nodes[name]["profile"] = {
            "cost": {
                "cpu": random.randint(1, 10),
                "ram": random.randint(1, 10),
                "storage": random.randint(1, 10),
            },
            "carbon": random.randint(1, 10),
        }
        nodes[name]["capabilities"] = {}
        for i in POSSIBILE_REQ_COMP:
            nodes[name]["capabilities"][i] = generate_dep(i,None,True)
    links = []
    for i in range(nodes_n):
        for j in range(i + 1, nodes_n):
            links.append(
                {
                    "connected_nodes": ["node" + str(i), "node" + str(j)],
                    "capabilities": {},
                }
            )
            for req in POSSIBILE_REQ_DEPENDENCY:
                links[-1]["capabilities"][req] = generate_dep(req,None,True)

    return {"name": fake.company(), "nodes": nodes, "links": links}
