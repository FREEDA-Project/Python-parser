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
        self.output.append("\n")

        flavours = list(set(e for f in struct.flavours.values() for e in f))
        self.output.append("Flavs = {" + ", ".join(f for f in flavours) + "};")
        self.output.append("Flav = [" + ", ".join(
            "{" + ", ".join(fs) + "}"
            for fs in struct.flavours.values()
        ) + "];")
        self.output.append("\n")

        self.output.append(self.make_importance(struct, flavours))
        self.output.append("\n")

        self.output.append(self.make_uses(struct))
        self.output.append("\n")

        self.output.append("%CRes = {};") # TODO: fix once you have the resources
        self.output.append("%NRes = {};") # TODO: fix once you have the resources

        self.output.append("MAX_BOUND = " + str(struct.max_bound) + ";")
        self.output.append("% worstBounds = [];") # TODO: fix once you have the resources
        self.output.append("bestBounds = [MAX_BOUND - i | i in worstBounds];")
        self.output.append("\n")

        self.output.append(self.make_component_requirement(struct))
        self.output.append("\n")

        self.output.append("Nodes = {" + ", ".join(struct.nodes) + "};\n")
        self.output.append(self.make_node_capabilities(struct))
        self.output.append("\n")

        self.output.append(self.make_dependency_requirement(struct))
        self.output.append("\n")

        self.output.append(self.make_link_capacity(struct))
        self.output.append("\n")

        self.output.append(self.make_cost(struct))
        self.output.append("\n")

        self.output.append(self.make_carb(struct))
        self.output.append("\n")

        self.output.append("costWeight = 0;")
        self.output.append("consWeight = 1;")

        self.output.append("costBudget = " + str(struct.cost_budget) + ";")
        self.output.append("carbBudget = " + str(struct.carbon_budget) + ";")
        self.output.append("\n")

    def make_importance(self, struct, flavours):
        result = "imp = array2d(Comps, Flavs, [\n"
        result += self.construct_element(
            struct.importance,
            [
                (struct.components, "Comps"),
                (flavours, "Flavs")
            ], True, lambda ciclers, values : " /\\ ".join(
                str(c) + " = " + str(v)
                for c, v in zip(ciclers, values)),
            lambda _1 : "0"
        )
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
            ], True, make_if_uses,
            lambda _1, _2 : "else " + str(0)
        )

        return result

    def make_component_requirement(self, struct):
        result = "comReq = array2d(CompFlavs, Res, [\n"
        compflavs_comreq = {
            (str(c) + "-" + str(f), r) : v
            for (c, f, r), v in struct.component_requirements.items()
        }
        def make_if_comreq(ciclers: list[str], values: list[str]):
            return " /\\ ".join(
                    str(c) + " = " + str(v)
                    for c, v in zip(ciclers, values)
            )
        comreq_body = self.construct_element(
            compflavs_comreq,
            [
                (self.compflavs, "CompFlavs"),
                (struct.resources, "Res")
            ], True, make_if_comreq,
            lambda _ : "MAX_BOUND"
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
            ], True, make_if_node_cap,
            lambda _ : "0"
        )
        result += node_cap
        return result

    def make_dependency_requirement(self, struct):
        result = "depReq = array4d(Comps, Flavs, Comps, Res, [\n"
        result += "\tif not(f1 in Flav[c1]) then\n\t\tworstBounds[r1]" # TODO: I do not know how to remove this "if" (the problem happens when we decide to build a matrix instead)
        result += "\n" + self.construct_element(
            struct.dependencies,
            [
                (struct.components, "Comps"),
                (struct.flavours, "Flavs"),
                (struct.components, "Comps"),
                (struct.resources, "Res")
            ], False, lambda ciclers, values : " /\\ ".join(
                str(c) + " = " + (str(v) if not str(c).startswith("r") else "N(" + str(v) + ")")
                for c, v in zip(ciclers, values)),
            lambda _1, _2 : "else worstBounds[r1]"
        )
        return result

    def make_link_capacity(self, struct):
        result = "linkCap = array3d(Nodes0, Nodes0, Res, [\n"
        result += " \tif ni = 0 \/ nj = 0 then\n\t\tbestBounds[r1]" # TODO: this ideally will be compiled and added when we have bestbounds for each resource

        def make_if_link_capacity(ciclers, values):
            n1, n2, r1 = ciclers
            v1, v2, vr = values
            return (
                "{" +
                    str(n1) + ", " + str(n2)
                + "} = {" +
                    str(v1) + ", " + str(v2)
                + "}" +  " /\\ " + str(r1) + " = N(" + str(vr) + ")"
            )

        result += "\n" + self.construct_element(
            struct.link_capacity,
            [
                (struct.components, "Comps"),
                (struct.components, "Comps"),
                (struct.resources, "Res")
            ], False, make_if_link_capacity,
            lambda _1, _2 : "else worstBounds[r1]"
        )
        return result

    def make_cost(self, struct):
        result = "cost = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n" # TODO: also this will be bestbounds
        result += self.construct_element(
            struct.node_cost,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ], True, lambda ciclers, values : " /\\ ".join(
                str(c) + " = " + str(v)
                for c, v in zip(ciclers, values)),
            lambda _1 : "0"
        )
        return result

    def make_carb(self, struct):
        result = "carb = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n"
        result += self.construct_element(
            struct.node_carb,
            [
                (struct.nodes, "Nodes"),
                (struct.resources, "Res")
            ], True, lambda ciclers, values : " /\\ ".join(
                str(c) + " = " + str(v)
                for c, v in zip(ciclers, values)),
            lambda _1 : "0"
        )
        return result

    def check_sparsity(self, matrix: dict, args) -> bool:
        max_elements = reduce(lambda x, y : x * len(y), args, 1)
        return len(matrix) / max_elements < 0.5

    def construct_element(
        self,
        values: dict,
        indexes: list[tuple[set, str]],
        first_if: bool,
        if_generator, #: Callable[list[str], tuple]
        no_value, #: Callable[list[str], list[str]] | Callable[tuple]
    ) -> str:
        if self.check_sparsity(values, [i[0] for i in indexes]):
            return self.construct_via_if(values, indexes, first_if, if_generator, no_value)
        else:
            return self.construct_explicit(values, indexes, no_value)

    def construct_via_if(
        self,
        values: dict,
        indexes: list[tuple[set, str]],
        first_if: bool,
        if_generator, #: Callable[list[str], tuple]
        if_finisher, #: Callable[list[str], list[str]]
    ) -> str:
        names = {}
        cicler_names = []
        finisher = []
        for _, n in indexes:
            if n not in names:
                names[n] = 0
            names[n] += 1

            cicler = n[0].lower() + str(names[n])
            cicler_names.append(cicler)
            finisher.append(cicler + " in " + n)

        body = []
        for i, (ks, v) in enumerate(values.items()):
            first_part = "\tif " if i == 0 and first_if else "\telseif "
            body.append(first_part + if_generator(cicler_names, ks) + " then " + str(v))

        body.append("\t" + if_finisher(cicler_names, [k for k, _ in values.items()]))
        body.append("\tendif | " +  ", ".join(finisher) + "\n]);")

        return "\n".join(body)

    def matrix_creator( # TODO: add types
        self,
        batched_indexes,
        indexes,
        values,
        n,
        no_value
    ):
        if n == 1:
            return (
                "\t" + ", ".join([
                    str(values[i]) if i in values else no_value(i)
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
        no_value # Callable[tuple]
        # TODO: no_value is a bit problematic: if it construct a "if" then it
        # will have 2 parameters, otherwise if matrix it will be one
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
