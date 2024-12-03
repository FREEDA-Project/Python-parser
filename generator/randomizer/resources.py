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
        bounds = (
            random.randint(0, max_value / 10),
            random.randint(max_value - (max_value / 10), max_value),
        )
        resources[name] = {
            "choices" : [
                name + "_" + str(i)
                for i in range(random.randint(0, amount))
            ],
            "optimization" : "minimization",
            "best_bound" : 0,
            "worst_bound" : 1
        } if kind[0] == "list" else {
            "type" : kind[0],
            "optimization" : "minimization",
            "best_bound": bounds[0],
            "worst_bound" : bounds[1]
        }

    return resources