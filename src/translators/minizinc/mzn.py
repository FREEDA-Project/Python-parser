from src.language.intermediate_language import IntermediateStructure
from src.translators.translator import Translator
from .utils import combine_comp_flav, construct_explicit

model_text = """
set of int: CompFlavs = 1..sum(c in Comps)(length(Flav[c]));

function int: Idx(Comps: c, Flavs: f) =
    sum (i in 1..c-1)(length(Flav[Comps[i]])) + arg_max([f = i | i in Flav[c]]);

enum Res = C(CRes) ++ N(NRes);

array[CompFlavs] of set of Res: Req_cf = [
    {r | r in Res where comReq[cf, r] != worstBounds[r]} | cf in CompFlavs
];

array[Comps, Flavs, Comps] of set of Res: Req_cfc = array3d(Comps, Flavs, Comps,
    [{r | r in Res where depReq[c1, i, c2, r] != worstBounds[r]}
    | c1 in Comps, i in Flavs, c2 in Comps
]);

set of int: Nodes0 = {0} union Nodes;

array[Nodes] of set of Res: Req_n = [
    {r | r in Res where nodeCap[n, r] != worstBounds[r]} | n in Nodes
];

constraint assert(forall(r in Res)(nodeCap[0,r] = bestBounds[r]),
    "Assertion nodeCap[0,r] = bestBounds[r] failed.", true);

constraint assert (forall(n in Nodes, r in Res)(
    linkCap[n,0,r] = bestBounds[r] /\ linkCap[0, n, r] = bestBounds[r]),
    "Assertion linkCap[n,0,r] = linkCap[0,n,r] = bestBounds[r] failed.", true);

constraint assert (forall(r in Res)(cost[0,r] = 0),
    "Assertion cost[0,r] = 0 failed.", true);

array [{0} union CompFlavs, Nodes0] of var 0..1: D;

array [Comps] of var Nodes0: node = [
    sum(i in Flav[c], j in Nodes)(j * D[Idx(c, i), j]) | c in Comps
];

var int: totCost = sum(c in Comps, i in Flav[c], r in Req_cf[Idx(c, i)])(
    comReq[Idx(c, i), r] * cost[node[c], r] * D[Idx(c, i), node[c]]
);

var int: totCarb = sum(
    n in Nodes0,
    c in Comps,
    i in Flav[c],
)(
    energy[Idx(c, i)] * carb[n] * D[Idx(c, i), n]
) + sum(
    cs in Comps,
    is in Flav[cs],
    cd in Comps where mayUse[cd, Idx(cs, is)] = 1
)(
    energy_dependency[cs, is, cd] * round((carb[node[cs]] + carb[node[cd]]) / 2)
);

constraint forall(j in Nodes0)(D[0, j] = 0);
constraint forall(i in CompFlavs)(D[i, 0] = 0);

constraint forall(c in Comps)(
    sum(i in Flav[c], j in Nodes)(D[Idx(c, i), j]) <= 1
);

constraint forall(m in mustComps)(
    sum (i in Flav[m], j in Nodes)(D[Idx(m, i), j]) > 0 /\ node[m] > 0
);

constraint forall(
    c in Comps,
    i in Flav[c],
    cu in Comps,
    iu in Flav[cu] where Uses[Idx(c, i), Idx(cu, iu)] = 1
)(
    sum(j in Nodes)(D[Idx(c, i), j]) <=
    sum(k in Flav[cu], j in Nodes where imp[cu,k] >= imp[cu,iu])(D[Idx(cu, k),j])
);

constraint forall(c in Comps diff mustComps)(
    sum(i in Flav[c], j in Nodes)(D[Idx(c, i), j]) <=
    sum(
        cs in Comps where c != cs,
        is in Flav[cs] where mayUse[c, Idx(cs, is)] = 1,
        j in Nodes
    )(D[Idx(cs, is), j])
);

constraint forall(j in Nodes, r in Req_n[j] where r in C(CRes)) (
    if worstBounds[r] = MIN_RBOUNDS then
        sum(c in Comps, i in Flav[c] where r in Req_cf[Idx(c,i)])
        (comReq[Idx(c,i), r] * D[Idx(c,i), j]) <= nodeCap[j,r]
    else
        assert(false, "·Lower bound for 'maximization' resources unsupported.")
    endif
);

constraint forall(
  c in Comps,
  i in Flav[c],
  r in Req_cf[Idx(c,i)] where r in N(NRes)
)(
    if worstBounds[r] = MIN_RBOUNDS then
        comReq[Idx(c,i), r] * D[Idx(c,i), node[c]] <= nodeCap[node[c], r]
    else
        comReq[Idx(c,i), r] >= nodeCap[node[c], r] * D[Idx(c,i), node[c]]
    endif
);

constraint forall(
    cs in Comps,
    is in Flav[cs],
    cd in Comps where mayUse[cd, Idx(cs, is)] = 1,
    r in Req_cfc[cs, is, cd] where r in N(NRes),
)(
    if worstBounds[r] = MIN_RBOUNDS then
        depReq[cs, is, cd, r] * sum(j in Nodes)(D[Idx(cs, is), j]) <=
        linkCap[node[cs], node[cd], r]
    else
        depReq[cs, is, cd, r] >= sum(j in Nodes)(D[Idx(cs, is), j]) *
        linkCap[node[cs], node[cd], r]
    endif
);

constraint totCost <= costBudget;
constraint totCarb <= carbBudget;

output [
    if fix(node[c]) > 0 then
        "Component \(c) deployed in flavour \([Flavs[i] | i in Flav[c] where D[Idx(c, i), node[c]] > 0][1]) on node \(Nodes[node[c]]).\\n"
    else
        "Component \(c) not deployed.\\n"
    endif
    | c in Comps
] ++ [
    "Objective value: \(obj)\\n\\tTotal cost: \(totCost)\\n\\tTotal carb: \(totCarb)"
];
"""

class MZNFirstPhaseTranslator(Translator):
    def __init__(self, structure: IntermediateStructure):
        super(MZNFirstPhaseTranslator, self).__init__(structure)

        self.comps_initial = "enum Comps = {"
        self.mustcomps_initial = "set of Comps: mustComps = {"
        self.flavs_initial = "enum Flavs = {"
        self.flav_initial = "array[Comps] of set of Flavs: Flav = ["
        self.importance_initial = "array[Comps, Flavs] of int: imp = array2d(Comps, Flavs, [\n"
        self.energy_initial = "array[CompFlavs] of int: energy = ["
        self.energy_dependency_initial = "array[Comps, Flavs, Comps] of int: energy_dependency;"
        self.uses_initial = "array[CompFlavs, CompFlavs] of 0..1: Uses = array2d(CompFlavs, CompFlavs, ["
        self.mayUse_initial = "array[Comps, CompFlavs] of 0..1: mayUse = array2d(Comps, CompFlavs, ["
        self.cres_initial = "enum CRes = {"
        self.nres_initial = "enum NRes = {"
        self.max_bound_initial = "int: MAX_RBOUNDS = "
        self.min_bound_initial = "int: MIN_RBOUNDS = "
        self.worst_bound_initial = "array[Res] of MIN_RBOUNDS..MAX_RBOUNDS: worstBounds = [\n"
        self.best_bound_initial = "array[Res] of MIN_RBOUNDS..MAX_RBOUNDS: bestBounds = [\n"
        self.comReq_initial = "array[CompFlavs, Res] of int: comReq = array2d(CompFlavs, Res, [\n"
        self.nodes_initial = "enum Nodes = {"
        self.nodeCap_initial = "array[Nodes0, Res] of int: nodeCap = array2d(Nodes0, Res,\n"
        self.depReq_initiale = "array[Comps, Flavs, Comps, Res] of int: depReq = array4d(Comps, Flavs, Comps, Res, [\n"
        self.linkCap_initial = "array[Nodes0, Nodes0, Res] of int: linkCap = array3d(Nodes0, Nodes0, Res, [\n"
        self.cost_initial = "array[Nodes0, Res] of int: cost = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n"
        self.carb_initial = "array[Nodes0] of int: carb = array1d(Nodes0, [0] ++ [ % No node\n"
        self.costbudget_initial = "int: costBudget = "
        self.carbbudget_initial = "int: carbBudget = "

        self.obj = [
            "var int: obj = sum(c in Comps, i in Flav[c])(",
            "\timp[c,i] * sum([D[Idx(c,i),j] | j in Nodes])",
            ");\nsolve maximize obj;"
        ]

        flavs_order = {e : i for i, e in enumerate(self.structure.flavs)}

        self.flavours = {
            c : sorted(f, key=lambda x: flavs_order.get(x, float('inf')))
            for c, f in self.structure.flavours.items()
        }

        self.compflavs = [
            combine_comp_flav(c, f)
            for c, fs in self.flavours.items()
            for f in fs
        ]

        self.output = [model_text]

    def translate(self):
        preamble = "%%% Input data for " + self.structure.app_name + " in " + self.structure.infrastructure_name + " %%%"
        self.output.extend([
            "%" * len(preamble),
            preamble,
            "%" * len(preamble)
        ])

        self.output.append(self.comps_initial + ", ".join(self.structure.components) + "};")
        self.output.append(self.mustcomps_initial + ", ".join(self.structure.must_components) + "};")

        self.output.append(self.flavs_initial + ", ".join(self.structure.flavs) + "};")
        self.output.append(self.flav_initial + ", ".join(
            "{" + ", ".join(fs) + "}"
            for fs in self.flavours.values()
        ) + "];")

        self.output.append(self.make_importance())

        self.output.append(self.make_energy())

        self.output.append(self.make_energy_dependency())

        self.output.append(self.make_uses())
        self.output.append(self.make_may_use())

        self.output.append(self.cres_initial + ", ".join(self.structure.consumable_resource) + "};")
        self.output.append(self.nres_initial + ", ".join(self.structure.non_consumable_resource) + "};")

        self.output.append(self.make_resources_bounds())

        self.output.append(self.make_component_requirement())

        self.output.append(self.nodes_initial + ", ".join(self.structure.nodes) + "};\n")
        self.output.append(self.make_node_capabilities())

        self.output.append(self.make_dependency_requirement())

        self.output.append(self.make_link_capacity())

        self.output.append(self.make_cost())

        self.output.append(self.make_carb())

        self.output.append(self.costbudget_initial + str(self.structure.cost_budget) + ";")
        self.output.append(self.carbbudget_initial + str(self.structure.carbon_budget) + ";")

        self.output.extend(self.obj)

        return self

    def make_importance(self):
        result = self.importance_initial
        result += construct_explicit(
            self.structure.importance,
            [
                (self.structure.components, "Comps"),
                (self.structure.flavs, "Flavs")
            ],
            lambda _ : "0"
        )
        return result

    def make_energy(self):
        compflavs_energy = {
            combine_comp_flav(c, f) : v
            for (c, f), v in self.structure.energy.items()
        }

        result = self.energy_initial
        result += ", ".join(str(compflavs_energy[cf]) for cf in self.compflavs) + "];"
        return result

    def make_energy_dependency(self):
        result = self.energy_dependency_initial
        result += "\n" + construct_explicit(
            self.structure.energy_dependencies,
            [
                (self.structure.components, "Comps"),
                (self.structure.flavs, "Flavs"),
                (self.structure.components, "Comps")
            ],
            lambda _ : "0"
        )
        return result

    def make_uses(self):
        result = self.uses_initial
        compflavs_uses = dict()
        for (c1, f1), uses_list in self.structure.uses.items():
            for (c2, f2) in uses_list:
                compflavs_uses[
                    combine_comp_flav(c1, f1),
                    combine_comp_flav(c2, f2)
                ] = str(1)

        result += "\n" + construct_explicit(
            compflavs_uses,
            [
                (self.compflavs, "CompFlavs"),
                (self.compflavs, "CompFlavs")
            ],
            lambda _ : "0"
        )

        return result

    def make_may_use(self):
        result = self.mayUse_initial

        mayUse = {}
        for c in self.structure.components:
            for c_prime in self.structure.components:
                for f_prime in self.flavours[c_prime]:
                    is_used = False
                    for f in self.flavours[c]:
                        if ((c_prime, f_prime) in self.structure.uses) and ((c, f) in self.structure.uses[(c_prime, f_prime)]):
                            is_used = True

                    if is_used:
                        mayUse.update({
                            (c, combine_comp_flav(c_prime, f_prime)): 1
                        })

        result += "\n" + construct_explicit(
            mayUse,
            [
                (self.structure.components, "Comps"),
                (self.compflavs, "CompFlavs")
            ],
            lambda _ : "0"
        )
        return result

    def make_resources_bounds(self):
        result = self.max_bound_initial + str(max(self.structure.worst_bounds.values())) + ";\n"
        result += self.min_bound_initial + str(min(self.structure.best_bounds.values())) + ";\n"

        result += self.worst_bound_initial + "".join(
            "\t" + ("MIN_RBOUNDS" if self.structure.resource_minimization[r] else "MAX_RBOUNDS") + ", % " + r + "\n"
            for r in self.structure.resources
        ) + "];\n"
        result += self.best_bound_initial + "".join(
            "\t" + ("MAX_RBOUNDS" if self.structure.resource_minimization[r] else "MIN_RBOUNDS") + ", % " + r + "\n"
            for r in self.structure.resources
        ) + "];\n"

        return result

    def make_component_requirement(self):
        result = self.comReq_initial
        compflavs_comreq = {
            (combine_comp_flav(c, f), r) : v
            for (c, f, r), v in self.structure.component_requirements.items()
        }

        comreq_body = construct_explicit(
            compflavs_comreq,
            [
                (self.compflavs, "CompFlavs"),
                (self.structure.resources, "Res")
            ],
            lambda i : "MIN_RBOUNDS" if self.structure.resource_minimization[i[-1]] else "MAX_RBOUNDS"
        )
        result += comreq_body
        return result

    def make_node_capabilities(self):
        result = self.nodeCap_initial
        result += "\t[bestBounds[r] | r in Res] ++ [ % No node\n"

        node_cap = construct_explicit(
            self.structure.node_capabilities,
            [
                (self.structure.nodes, "Nodes"),
                (self.structure.resources, "Res")
            ],
            lambda _ : "0"
        )
        result += node_cap
        return result

    def make_dependency_requirement(self):
        result = self.depReq_initiale
        result += construct_explicit(
            self.structure.dependencies,
            [
                (self.structure.components, "Comps"),
                (self.structure.flavs, "Flavs"),
                (self.structure.components, "Comps"),
                (self.structure.resources, "Res")
            ],
            lambda i : "MIN_RBOUNDS" if self.structure.resource_minimization[i[-1]] else "MAX_RBOUNDS"
        )
        return result

    def make_link_capacity(self):
        for n in self.structure.nodes:
            for r in self.structure.resources:
                if (n, n, r) not in self.structure.link_capacity.keys():
                    if (n, r) in self.structure.node_capabilities:
                        self.structure.link_capacity[(n, n, r)] = self.structure.node_capabilities[(n, r)]
                    else:
                        self.structure.link_capacity[(n, n, r)] = '0'

        def make_bounds(indexes):
            resource = indexes[-1]
            if indexes[0] == "0" or indexes[1] == "0":
                return "MAX_RBOUNDS" if self.structure.resource_minimization[resource] else "MIN_RBOUNDS"
            else:
                return "MIN_RBOUNDS" if self.structure.resource_minimization[resource] else "MAX_RBOUNDS"

        result = self.linkCap_initial
        result += construct_explicit(
            self.structure.link_capacity,
            [
                (["0"] + self.structure.nodes, "Nodes0"),
                (["0"] + self.structure.nodes, "Nodes0"),
                (self.structure.resources, "Res")
            ],
            make_bounds
        )
        return result

    def make_cost(self):
        result = self.cost_initial
        result += construct_explicit(
            self.structure.node_cost,
            [
                (self.structure.nodes, "Nodes"),
                (self.structure.resources, "Res")
            ],
            lambda _ : "0"
        )
        return result

    def make_carb(self):
        result = self.carb_initial
        result += ", ".join(str(self.structure.node_carb[n]) for n in self.structure.nodes) + "\n]);"
        return result

    def to_string(self) -> str:
        return "\n".join(self.output)


class MZNSecondPhaseTranslator(MZNFirstPhaseTranslator):
    def __init__(self, structure):
        super(MZNSecondPhaseTranslator, self).__init__(structure)

        # Override objective function
        self.obj = [
            "var int: obj = sum(",
            "\tc in Comps,",
            "\ti in Flav[c],",
            "\tj in Nodes where D_old[Idx(c, i), j] = 1",
            ")(",
            "\tD[Idx(c, i), j]",
            ");\n\nsolve maximize obj;"
        ]

    def translate(self):
        super().translate()

        D_old = {
            (combine_comp_flav(c, f), n) : 1
            for (c, f), n in self.structure.old_deployment.items()
        }

        old_deployment = (
            "array[CompFlavs, Nodes] of 0..1: D_old = array2d(CompFlavs, Nodes, [\n"
            + construct_explicit(
                D_old,
                [
                    (self.compflavs, "CompFlavs"),
                    (self.structure.nodes, "Nodes")
                ],
                lambda _ : "0"
            )
        )
        self.output.append(old_deployment)

        for (c, f), nodes in self.structure.constraints["avoid"].items():
            for n in nodes:
                self.output.append(
                    f"constraint D[Idx({c}, {f}), {n}] = 0;"
                )
        for (c1, f1), list_tuple_comp_flavs in self.structure.constraints["affinity"].items():
            for c2, f2 in list_tuple_comp_flavs:
                self.output.append(
                    f"constraint D[Idx({c1}, {f1}), node[{c1}]] = D[Idx({c2}, {f2}), node[{c2}]];"
                )
        for (c1, f1), list_tuple_comp_flavs in self.structure.constraints["antiaffinity"].items():
            for c2, f2 in list_tuple_comp_flavs:
                self.output.append(
                    f"constraint D[Idx({c1}, {f1}), node[{c1}]] != D[Idx({c2}, {f2}), node[{c2}]];"
                )

        return self
