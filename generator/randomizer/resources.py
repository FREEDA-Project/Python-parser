import random

def generate_resources(amount, max_value):
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
            random.randint(0, max_value / 10),
            random.randint(max_value - (max_value / 10), max_value),
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