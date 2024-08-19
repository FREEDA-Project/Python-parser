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

    def __init__(self, struct: IntermediateStructure):
        super(MiniZincTranslator, self).__init__(struct)

        self.compflavs = [
            str(c) + "-" + str(f)
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

    def make_if_generic(self, struct, ciclers, values):
        result = []
        for c, v in zip(ciclers, values):
            l = "C" if str(v) in struct.consumable_resource else "N"
            value = v if not c.startswith("r") else l + "(" + str(v) + ")"
            result.append(c + " = " + value)

        return " /\\ ".join(result)

    def make_importance(self, struct, flavours):
        result = "imp = array2d(Comps, Flavs, [\n"
        result += self.construct_element(
            struct.importance,
            [
                (struct.components, "Comps"),
                (flavours, "Flavs")
            ],
            {
                "first_if": True,
                "if_generator": lambda ciclers, values : " /\\ ".join(
                    str(c) + " = " + str(v)
                    for c, v in zip(ciclers, values)
                ),
                "no_value_if" : lambda _1, _2 : "else 0",
                "no_value_matrix" : lambda _ : "0"
            }
        )
        return result

    def make_resources_bounds(self, struct):
        result = "MAX_RBOUNDS = " + str(struct.max_bound) + ";\n"
        result += "MIN_RBOUNDS = " + str(struct.min_bound) + ";\n"
        worst_list = []
        best_list = []
        for r in struct.resources:
            worst = (
                struct.worst_bounds[r]
                if r in struct.worst_bounds
                else struct.max_bound - struct.best_bounds[r]
            )
            best = (
                struct.best_bounds[r]
                if r in struct.best_bounds
                else struct.max_bound - struct.worst_bounds[r]
            )
            worst_list.append(str(worst))
            best_list.append(str(best))

        result += "worstBounds = [" + ", ".join(worst_list) + "];\n"
        result += "bestBounds = [" + ", ".join(best_list) + "];\n"
        return result

    def make_uses(self, struct):
        result = "Uses = array2d(CompFlavs, CompFlavs, ["
        compflavs_uses = dict()
        for (c1, f1), (c2, f2) in struct.uses.items():
            compflavs_uses[
                str(c1) + "-" + str(f1),
                str(c2) + "-" + str(f2)
            ] = str(1)

        def make_if_uses(ciclers: list[str], values: list[str]):
            indexes = [self.compflavs.index(v) + 1 for v in values]
            return " /\\ ".join(
                    str(c) + " = " + str(v)
                    for c, v in zip(ciclers, indexes)
            )
        result += "\n" + self.construct_element(
            compflavs_uses,
            [
                (self.compflavs, "CompFlavs"),
                (self.compflavs, "CompFlavs")
            ],
            {
                "first_if": True,
                "if_generator": make_if_uses,
                "no_value_if": lambda _1, _2 : "else 0",
                "no_value_matrix": lambda _ : "0"
            }
        )

        return result

    def make_may_use(self, struct):
        result = "mayUse = array2d(Comps, CompFlavs, ["
        mayUse = {
            (ct, str(cf) + "-" + str(ff)) : 1
            for (cf, ff), (ct, _) in struct.uses.items()
        }
        def make_if_may_uses(ciclers: list[str], values: list[str]):
            return (
                str(ciclers[0]) + " = " + str(values[0])
                + " /\\ " +
                str(ciclers[1]) + " = " + str(self.compflavs.index(values[1]))
            )
        result += "\n" + self.construct_element(
            mayUse,
            [
                (struct.components, "Comps"),
                (self.compflavs, "CompFlavs")
            ],
            {
                "first_if": True,
                "if_generator": make_if_may_uses,
                "no_value_if": lambda _1, _2 : "else 0",
                "no_value_matrix": lambda _ : "0"
            }
        )
        return result

    def make_component_requirement(self, struct):
        result = "comReq = array2d(CompFlavs, Res, [\n"
        compflavs_comreq = {
            (str(c) + "-" + str(f), r) : v
            for (c, f, r), v in struct.component_requirements.items()
        }
        def make_if_comreq(ciclers, values):
            result = []
            for c, v in zip(ciclers, values):
                if c.startswith("c") and v in self.compflavs:
                    value = str(self.compflavs.index(v))
                elif c.startswith("r") and v in struct.consumable_resource:
                    value = "C(" + v + ")"
                elif c.startswith("r") and v in struct.non_consumable_resource:
                    value = "N(" + v + ")"

                result.append(c + " = " + value)

            return " /\\ ".join(result)
        comreq_body = self.construct_element(
            compflavs_comreq,
            [
                (self.compflavs, "CompFlavs"),
                (struct.resources, "Res")
            ],
            {
                "first_if": True,
                "if_generator": make_if_comreq,
                "no_value_if": lambda _1, _2 : "else worstBounds[r1]",
                "no_value_matrix": lambda r :
                    struct.worst_bounds[r[1]] if r[1] in struct.worst_bounds else struct.best_bounds[r[1]]
            }
        )
        result += comreq_body
        return result

    def make_node_capabilities(self, struct):
        result = "nodeCap = array2d(Nodes0, Res,\n"
        result += "\t[bestBounds[r] | r in Res] ++ [ % No node\n"
        def make_if_node_cap(ciclers: list[str], values: list[str]):
            return " /\\ ".join(
                    str(c) + " = " + str(v)
                    for c, v in zip(ciclers, values)
            )
        node_cap = self.construct_element(
            struct.node_capabilities,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ],
            {
                "first_if": True,
                "if_generator": make_if_node_cap,
                "no_value_if": lambda _1, _2 : "else 0",
                "no_value_matrix": lambda _ : "0"
            }
        )
        result += node_cap
        return result

    def make_dependency_requirement(self, struct):
        result = "depReq = array4d(Comps, Flavs, Comps, Res, [\n"
        result += self.construct_element(
            struct.dependencies,
            [
                (struct.components, "Comps"),
                (struct.flavours, "Flavs"),
                (struct.components, "Comps"),
                (struct.resources, "Res")
            ],
            {
                "first_if": True,
                "if_generator": lambda c, v : self.make_if_generic(struct, c, v),
                "no_value_if": lambda _1, _2 : "else worstBounds[r1]",
                "no_value_matrix": lambda _ : "MAX_BOUND"
            }
        )
        return result

    def make_link_capacity(self, struct):
        result = "linkCap = array3d(Nodes0, Nodes0, Res, [\n"
        result += " \tif n1 = n2 then\n\t\tnodeCap[n1, r1]\n"
        result += " \telseif n1 = 0 \/ n2 = 0 then\n\t\tbestBounds[r1]"
        result += "\n" + self.construct_element(
            struct.link_capacity,
            [
                (struct.nodes, "Nodes0"),
                (struct.nodes, "Nodes0"),
                (struct.resources, "Res")
            ],
            {
                "if_generator": lambda c, v : self.make_if_generic(struct, c, v),
                "no_value_if": lambda _1, _2 : "else worstBounds[r1]",
                "no_value_matrix": lambda _ : "MAX_BOUND"
            }
        )
        return result

    def make_cost(self, struct):
        result = "cost = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n"
        result += self.construct_element(
            struct.node_cost,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ],
            {
                "first_if": True,
                "if_generator": lambda c, v : self.make_if_generic(struct, c, v),
                "no_value_if": lambda _1, _2 : "else 0",
                "no_value_matrix": lambda _ : "0"
            }
        )
        return result

    def make_carb(self, struct):
        result = "carb = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n"
        result += self.construct_element(
            struct.node_carb,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ],
            {
                "first_if": True,
                "if_generator": lambda c, v : self.make_if_generic(struct, c, v),
                "no_value_if": lambda _1, _2 : "else 0",
                "no_value_matrix": lambda _ : "0"
            }
        )
        return result

    def check_sparsity(self, matrix: dict, args) -> bool:
        max_elements = reduce(lambda x, y : x * len(y), args, 1)
        return len(matrix) / max_elements < 0.5

    def construct_element(
        self,
        values: dict,
        indexes: list[tuple[set, str]],
        options: dict[Any, Any]
    ) -> str:
        if self.check_sparsity(values, [i[0] for i in indexes]):
            no_value = options["no_value_if"]
            first_if = True if "first_if" in options and options["first_if"] else False
            if_generator = options["if_generator"]
            return self.construct_via_if(values, indexes, first_if, if_generator, no_value)
        else:
            no_value = options["no_value_matrix"]
            return self.construct_explicit(values, indexes, no_value)

    def construct_via_if(
        self,
        values: dict,
        indexes: list[tuple[set, str]],
        first_if: bool,
        if_generator: Callable[[list[str], tuple], str],
        if_finisher: Callable[[list[str], list[str]], str]
    ) -> str:
        names = {}
        cicler_names = []
        finisher = []
        for _, n in indexes:
            name = n[0]
            if name not in names:
                names[name] = 0
            names[name] += 1

            cicler = name.lower() + str(names[name])
            cicler_names.append(cicler)
            finisher.append(cicler + " in " + n)

        ending = "| " +  ", ".join(finisher) + "\n]);"

        body = []

        if len(values) == 0:
            body.append(
                "\t" + if_finisher(cicler_names, [k for k, _ in values.items()])[5:] # remove the else
            )
            body.append("\t" + ending)
            return "\n".join(body)

        for i, (ks, v) in enumerate(values.items()):
            first_part = "\tif " if i == 0 and first_if else "\telseif "
            body.append(first_part + if_generator(cicler_names, ks) + " then " + str(v))

        body.append("\t" + if_finisher(cicler_names, [k for k, _ in values.items()]))
        body.append("\tendif " + ending)

        return "\n".join(body)

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
                ]) + ", % " + str(batched_indexes[0][0])
            )
        if n == 2:
            return (
                "\t%" + ", ".join(indexes[n - 1][0]) + "\n" +
                "\n".join([
                    self.matrix_creator(i, indexes, values, n - 1, no_value)
                    for i in batched_indexes
                ])
            )

        for e in batched_indexes:
            return (
                "% " + str(indexes[n - 1][0]) +
                "\n" + self.matrix_creator(e, indexes, values, n - 1, no_value)
            )

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
