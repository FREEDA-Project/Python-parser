from typing import Any, Callable
from functools import reduce
from itertools import product

from src.language.intermediate_language import IntermediateStructure
from src.translators.translator import Translator

class MiniZincTranslator(Translator):
    def batcher(iterable, n):
        result = []
        i = 0
        while i < len(iterable):
            result.append(iterable[i:i+n])
            i += n
        return result

    def combine_comp_flav(self, c, f):
        separator = "-"
        return str(c) + separator + str(f)

    def __init__(self, struct: IntermediateStructure):
        super(MiniZincTranslator, self).__init__(struct)

        self.compflavs = [
            self.combine_comp_flav(c, f)
            for c, fs in struct.flavours.items()
            for f in fs
        ]

        self.output = []

        preamble = "%%% Input data for " + struct.app_name + " in " + struct.infrastructure_name + " %%%"
        self.output.extend([
            "%" * len(preamble),
            preamble,
            "%" * len(preamble)
        ])

        self.output.append("Comps = {" + ", ".join(struct.components) + "};")
        self.output.append("mustComps = {" + ", ".join(struct.must_components) + "};")

        flavours = list(set(e for f in struct.flavours.values() for e in f))
        self.output.append("Flavs = {" + ", ".join(f for f in flavours) + "};")
        self.output.append("Flav = [" + ", ".join(
            "{" + ", ".join(fs) + "}"
            for fs in struct.flavours.values()
        ) + "];")

        self.output.append(self.make_importance(struct, flavours))

        self.output.append(self.make_uses(struct))
        self.output.append(self.make_may_use(struct))

        self.output.append("CRes = {" + ", ".join(struct.consumable_resource) + "};")
        self.output.append("NRes = {" + ", ".join(struct.non_consumable_resource) + "};")

        self.output.append(self.make_resources_bounds(struct))

        self.output.append(self.make_component_requirement(struct))

        self.output.append("Nodes = {" + ", ".join(struct.nodes) + "};\n")
        self.output.append(self.make_node_capabilities(struct))

        self.output.append(self.make_dependency_requirement(struct))

        self.output.append(self.make_link_capacity(struct))

        self.output.append(self.make_cost(struct))

        self.output.append(self.make_carb(struct))

        self.output.append("costBudget = " + str(struct.cost_budget) + ";")
        self.output.append("carbBudget = " + str(struct.carbon_budget) + ";")

    def make_importance(self, struct, flavours):
        result = "imp = array2d(Comps, Flavs, [\n"
        result += self.construct_explicit(
            struct.importance,
            [
                (struct.components, "Comps"),
                (flavours, "Flavs")
            ],
            lambda _ : "0"
        )
        return result

    def make_resources_bounds(self, struct):
        result = "MAX_RBOUNDS = " + str(max(struct.worst_bounds.values())) + ";\n"
        result += "MIN_RBOUNDS = " + str(min(struct.best_bounds.values())) + ";\n"

        result += "worstBounds = [\n" + "".join(
            "\t" + ("MIN_RBOUNDS" if struct.resource_minimization[r] else "MAX_RBOUNDS") + ", % " + r + "\n"
            for r in struct.resources
        ) + "];\n"
        result += "bestBounds = [\n" + "".join(
            "\t" + ("MAX_RBOUNDS" if struct.resource_minimization[r] else "MIN_RBOUNDS") + ", % " + r + "\n"
            for r in struct.resources
        ) + "];\n"

        return result

    def make_uses(self, struct):
        result = "Uses = array2d(CompFlavs, CompFlavs, ["
        compflavs_uses = dict()
        for (c1, f1), uses_list in struct.uses.items():
            for (c2, f2) in uses_list:
                compflavs_uses[
                    self.combine_comp_flav(c1, f1),
                    self.combine_comp_flav(c2, f2)
                ] = str(1)

        result += "\n" + self.construct_explicit(
            compflavs_uses,
            [
                (self.compflavs, "CompFlavs"),
                (self.compflavs, "CompFlavs")
            ],
            lambda _ : "0"
        )

        return result

    def make_may_use(self, struct):
        result = "mayUse = array2d(Comps, CompFlavs, ["
        mayUse = {
            (ct, self.combine_comp_flav(cf, ff)) : 1
            for (cf, ff), uses_list in struct.uses.items()
            for ct, _ in uses_list
        }

        result += "\n" + self.construct_explicit(
            mayUse,
            [
                (struct.components, "Comps"),
                (self.compflavs, "CompFlavs")
            ],
            lambda _ : "0"
        )
        return result

    def make_component_requirement(self, struct):
        result = "comReq = array2d(CompFlavs, Res, [\n"
        compflavs_comreq = {
            (self.combine_comp_flav(c, f), r) : v
            for (c, f, r), v in struct.component_requirements.items()
        }

        comreq_body = self.construct_explicit(
            compflavs_comreq,
            [
                (self.compflavs, "CompFlavs"),
                (struct.resources, "Res")
            ],
            lambda i : "MIN_RBOUNDS" if struct.resource_minimization[i[-1]] else "MAX_RBOUNDS"
        )
        result += comreq_body
        return result

    def make_node_capabilities(self, struct):
        result = "nodeCap = array2d(Nodes0, Res,\n"
        result += "\t[bestBounds[r] | r in Res] ++ [ % No node\n"

        node_cap = self.construct_explicit(
            struct.node_capabilities,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ],
            lambda _ : "0"
        )
        result += node_cap
        return result

    def make_dependency_requirement(self, struct):
        flavs = list({f for flavs in struct.flavours.values() for f in flavs})
        result = "depReq = array4d(Comps, Flavs, Comps, Res, [\n"

        result += self.construct_explicit(
            struct.dependencies,
            [
                (struct.components, "Comps"),
                (flavs, "Flavs"),
                (struct.components, "Comps"),
                (struct.resources, "Res")
            ],
            lambda i : "MIN_RBOUNDS" if struct.resource_minimization[i[-1]] else "MAX_RBOUNDS"
        )
        return result

    def make_link_capacity(self, struct):
        for n in struct.nodes:
            for r in struct.resources:
                if (n, n, r) not in struct.link_capacity.keys():
                    if (n, r) in struct.node_capabilities:
                        struct.link_capacity[(n, n, r)] = struct.node_capabilities[(n, r)]
                    else:
                        struct.link_capacity[(n, n, r)] = '0'

        def make_bounds(indexes):
            resource = indexes[-1]
            if indexes[0] == "0" or indexes[1] == "0":
                return "MAX_RBOUNDS" if struct.resource_minimization[resource] else "MIN_RBOUNDS"
            else:
                return "MIN_RBOUNDS" if struct.resource_minimization[resource] else "MAX_RBOUNDS"

        result = "linkCap = array3d(Nodes0, Nodes0, Res, [\n"
        result += self.construct_explicit(
            struct.link_capacity,
            [
                (["0"] + struct.nodes, "Nodes0"),
                (["0"] + struct.nodes, "Nodes0"),
                (struct.resources, "Res")
            ],
            make_bounds
        )
        return result

    def make_cost(self, struct):
        result = "cost = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n"
        result += self.construct_explicit(
            struct.node_cost,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ],
            lambda _ : "0"
        )
        return result

    def make_carb(self, struct):
        result = "carb = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n"
        result += self.construct_explicit(
            struct.node_carb,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ],
            lambda _ : "0"
        )
        return result

    def matrix_creator(
        self,
        batched_indexes: list[tuple],
        indexes: list[tuple[set, str]],
        values: dict,
        n: int,
        no_value: Callable[[int], str]
    ):
        if n == 1:
            return (
                "\t" + ", ".join([
                    str(values[i]) if i in values else str(no_value(i))
                    for i in batched_indexes
                ]) + ", % " + str(batched_indexes[0][-2])
            )
        if n == 2:
            return (
                "\t%" + ", ".join(indexes[-1][0]) + "\n" +
                "\n".join([
                    self.matrix_creator(i, indexes, values, n - 1, no_value)
                    for i in batched_indexes
                ])
            )

        result = ""
        for i, e in enumerate(batched_indexes):
            idxs = indexes[0][0]
            idx = list(idxs.keys())[i] if isinstance(idxs, dict) else idxs[i]

            result += (
                "\n\t% " + idx +
                "\n" + self.matrix_creator(e, indexes[1:], values, n - 1, no_value) +
                "\n"
            )
        return result

    def construct_explicit(
        self,
        values: dict,
        indexes: list[tuple[set, str]],
        no_value: Callable[[int], str]
    ) -> str:
        only_indexes = list(product(*(i[0] for i in indexes)))
        batched_indexes = only_indexes
        for index_values, _ in list(reversed(indexes))[:-1]:
            batched_indexes = MiniZincTranslator.batcher(batched_indexes, len(index_values))

        return self.matrix_creator(
            batched_indexes,
            indexes,
            values,
            len(indexes),
            no_value
        ) + "\n]);"

    def to_string(self) -> str:
        return "\n".join(self.output)
