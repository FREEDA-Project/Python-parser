from src.language.intermediate_language import IntermediateStructure
from src.translators.translator import Translator

class MOFTranslator(Translator): # MiniZinc Optimized Format
    def combine_comp_flav(self, c, f) -> str:
        separator = "_"
        return str(c) + separator + str(f)

    def make_d(self, c, i, j) -> str:
        return "D[" + self.combine_comp_flav(c, i) + ", " + j + "]"

    def __init__(self, struct: IntermediateStructure):
        super(MOFTranslator, self).__init__(struct)

        flavs_order = {e : i for i, e in enumerate(struct.flavs)}

        self.flavours = {
            c : sorted(f, key=lambda x: flavs_order.get(x, float('inf')))
            for c, f in struct.flavours.items()
        }

        self.compflavs = {
            (c, f) : self.combine_comp_flav(c, f)
            for c, fs in self.flavours.items()
            for f in fs
        }

        self.zero_node = "0"
        self.nodes0 = [self.zero_node] + struct.nodes

        mx = max(struct.worst_bounds.values())
        mn = min(struct.best_bounds.values())
        self.wbounds = {
            r : mn if struct.resource_minimization[r] else mx
            for r in struct.resources
        }

        self.output = []

        preamble = "%%% MZN optimazed for " + struct.app_name + " in " + struct.infrastructure_name + " %%%"
        self.output.extend([
            "%" * len(preamble),
            preamble,
            "%" * len(preamble),
            ""
        ])

        self.mayUse = {}
        for c in struct.components:
            for c_prime in struct.components:
                for f_prime in self.flavours[c_prime]:
                    is_used = False
                    for f in self.flavours[c]:
                        if ((c_prime, f_prime) in struct.uses) and ((c, f) in struct.uses[(c_prime, f_prime)]):
                            is_used = True

                    if is_used:
                        self.mayUse.update({
                            (c, self.combine_comp_flav(c_prime, f_prime)): 1
                        })

        self.output.append("enum Comps = {" + ", ".join(struct.components) + "};")
        self.output.append("set of Comps: mustComps = {" + ", ".join(struct.must_components) + "};")

        self.output.append("enum Flavs = {" + ", ".join(struct.flavs) + "};")
        self.output.append("array[Comps] of set of Flavs: Flav = [" + ", ".join(
            "{" + ", ".join(fs) + "}"
            for fs in self.flavours.values()
        ) + "];")

        self.output.append("enum CompFlavs = {" + ", ".join(self.compflavs.values()) + "};")
        self.output.append("enum CRes = {" + ", ".join(struct.consumable_resource) + "};")
        self.output.append("enum NRes = {" + ", ".join(struct.non_consumable_resource) + "};")
        self.output.append("enum Nodes = {" + ", ".join(struct.nodes) + "};")
        self.output.append("set of int: Nodes0 = {" + self.zero_node + "} union Nodes;\n")

        self.output.append("array [{0} union CompFlavs, Nodes0] of var 0..1: D;")
        self.output.append("var int: totCost = " + self.tot_quantity(struct, struct.node_cost) + ";")
        self.output.append("var int: totCarb = " + self.tot_quantity(struct, struct.node_carb) + ";")
        self.output.append(self.make_obj(struct))
        self.output.append("solve maximize obj;")
        self.output.append("""
function int: Idx(Comps: c, Flavs: f) = sum (i in 1..c-1)(length(Flav[Comps[i]])) + arg_max([f = i | i in Flav[c]]);
output [
  if exists(i in Flav[c], j in Nodes0)(fix(D[Idx(c, i), j]) > 0) then
    let {
      int: f = [Flavs[i] | i in Flav[c] where exists(j in Nodes0)(fix(D[Idx(c, i), j]) > 0)][1],
      int: n = [j | j in Nodes0 where exists(i in Flav[c])(fix(D[Idx(c, i), j]) > 0)][1]
    } in
    "Component \(c) deployed in flavour \(Flavs[f]) on node \(Nodes[n]).\\n"
  else
    "Component \(c) not deployed.\\n"
  endif
  | c in Comps
] ++ [
  "Objective value: \(obj)\\n\\tTotal cost: \(totCost)\\n\\tTotal carb: \(totCarb)"
];\n""")

        self.constraints = []
        self.constraints.append("totCost <= " + str(struct.cost_budget))
        self.constraints.append("totCarb <= " + str(struct.carbon_budget))
        self.constraints.extend(self.zero_values())
        self.constraints.extend(self.at_most_one(struct))
        self.constraints.extend(self.must_deploy(struct))
        self.constraints.extend(self.bigger_or_equal(struct))
        self.constraints.extend(self.target_not_in_mustcomps(struct))
        self.constraints.extend(self.sufficient_quantity(struct))
        self.constraints.extend(self.certain_amount(struct))
        self.constraints.extend(self.non_consumable_dependency(struct))

        for c in self.constraints:
            self.output.append("constraint " + c + ";")

    def make_importance(self, struct):
        result = "array[Comps, Flavs] of int: imp = array2d(Comps, Flavs, [\n"
        result += self.construct_explicit(
            struct.importance,
            [
                (struct.components, "Comps"),
                (struct.flavs, "Flavs")
            ],
            lambda _ : "0"
        )
        return result

    def tot_quantity(self, struct, quantity):
        to_sum = []
        for (c, f, r), v in struct.component_requirements.items():
            for n in struct.nodes:
                if (n, r) in quantity and quantity[(n, r)] != self.wbounds[r]:
                    to_sum.append(
                        str(v * quantity[n, r])
                        + " * "
                        + self.make_d(c, f, n)
                    )

        return "\n\t+ ".join(to_sum)

    def zero_values(self):
        result = [
            "D[" + self.zero_node + ", " + j + "] = 0"
            for j in self.nodes0
        ]

        for i in self.compflavs.values():
            result.append("D[" + str(i) + ", " + self.zero_node + "] = 0")

        return result

    def at_most_one(self, struct):
        result = []

        for c in struct.components:
            e = []
            for f in self.flavours[c]:
                for j in struct.nodes:
                    e.append(self.make_d(c, f, j))
            result.append("\n\t+ ".join(e) + "\n\t<= 1")

        return result

    def must_deploy(self, struct):
        result = []

        for c in struct.must_components:
            e = []
            for f in self.flavours[c]:
                for j in struct.nodes:
                    e.append(self.make_d(c, f, j))
            result.append("\n\t+ ".join(e) + "\n\t> 0")# /\\ node[" + c + "] > 0")

        return result

    def bigger_or_equal(self, struct):
        result = []

        for c in struct.components:
            for i in self.flavours[c]:
                for cu in struct.components:
                    for iu in self.flavours[cu]:
                        if (c, i) in struct.uses and (cu, iu) in struct.uses[(c, i)]:

                            lhs = []
                            for j in struct.nodes:
                                lhs.append(self.make_d(c, i, j))

                            rhs = []
                            for k in self.flavours[cu]:
                                if struct.importance[(cu, k)] >= struct.importance[(cu, iu)]:
                                    for j in struct.nodes:
                                        rhs.append(self.make_d(cu, k, j))

                            result.append("\n\t+ ".join(lhs) + "\n\t<=\n\t" + "\n\t+ ".join(rhs))
        return result

    def target_not_in_mustcomps(self, struct):
        result = []

        for c in struct.components:
            lhs = []
            if c not in struct.must_components:
                for f in self.flavours[c]:
                    for j in struct.nodes:
                        lhs.append(self.make_d(c, f, j))

                rhs = []
                for cs in struct.components:
                    if c != cs:
                        for fs in self.flavours[cs]:
                            comb = self.combine_comp_flav(cs, fs)
                            if (c, comb) in self.mayUse and self.mayUse[(c, comb)] == 1:
                                for j in struct.nodes:
                                    rhs.append(self.make_d(cs, fs, j))

                result.append(
                    "\n\t+ ".join(lhs) + "\n\t<=\n\t" + "\n\t+ ".join(rhs)
                )
        return result

    def sufficient_quantity(self, struct):
        result = []
        for j in struct.nodes:
            for r in struct.consumable_resource:
                lhs = []
                if (j, r) in struct.node_capabilities:
                    if struct.resource_minimization[r]:
                        for c in struct.components:
                            for i in self.flavours[c]:
                                if (c, i, r) in struct.component_requirements:
                                    lhs.append(
                                        str(struct.component_requirements[(c, i, r)])
                                        + " * " + self.make_d(c, i, j)
                                    )
                    else:
                        raise ValueError("Consumable 'maximization' resources unsupported")

                if len(lhs) > 0:
                    result.append("\n\t+ ".join(lhs) + "\n\t<= " + str(struct.node_capabilities[(j, r)]))

        return result

    def certain_amount(self, struct):
        ncap = struct.node_capabilities | {
            ('0', r) : struct.best_bounds[r]
            for r in struct.resources
        }

        result = []
        for j in self.nodes0:
            for c in struct.components:
                for i in self.flavours[c]:
                    for r in struct.non_consumable_resource:
                        if (c, i, r) in struct.component_requirements and struct.component_requirements[(c, i, r)] != self.wbounds[r]:
                            if struct.resource_minimization[r]:
                                result.append(
                                    str(struct.component_requirements[(c, i, r)])
                                    + " * "
                                    + self.make_d(c, i, j)
                                    + " <= "
                                    + str(ncap[(j, r)] if (j, r) in ncap else 0)
                                )
                            else:
                                result.append(
                                    str(struct.component_requirements[(c, i, r)])
                                    + " >= "
                                    + self.make_d(c, i, j)
                                    + " * "
                                    + str(ncap[(j, r)] if (j, r) in ncap else 0)
                                    + " * "
                                    + self.make_d(c, i, j)
                                )

        return result

    def non_consumable_dependency(self, struct):
        max_rbound = max(struct.worst_bounds.values())
        min_rboud = min(struct.best_bounds.values())
        lcap = struct.link_capacity | {
            ('0', '0', r) : max_rbound if struct.resource_minimization[r] else min_rboud
            for r in struct.resources
        } | {
            ('0', n, r) : min_rboud if struct.resource_minimization[r] else max_rbound
            for r in struct.resources
            for n in struct.nodes
        } | {
            (n, '0', r) : min_rboud if struct.resource_minimization[r] else max_rbound
            for r in struct.resources
            for n in struct.nodes
        } | {
            (n, n, r) : min_rboud if struct.resource_minimization[r] else max_rbound
            for r in struct.resources
            for n in struct.nodes
        }

        result = []
        for js in self.nodes0:
          for jd in self.nodes0:
            for r in struct.non_consumable_resource:
              if (js, jd, r) in lcap and lcap[(js, jd, r)] != self.wbounds[r]:
                for cs in struct.components:
                  for fs in self.flavours[cs]:
                    for cd in struct.components:
                      for fd in self.flavours[cd]:
                        if (cd, self.combine_comp_flav(cs, fs)) in self.mayUse and self.mayUse[(cd, self.combine_comp_flav(cs, fs))] == 1:
                          if (cs, fs, cd, r) in struct.dependencies and struct.dependencies[(cs, fs, cd, r)] != self.wbounds[r]:
                            if struct.resource_minimization[r]:
                              result.append(
                                str(struct.dependencies[(cs, fs, cd, r)])
                                + " * " + self.make_d(cs, fs, js)
                                + " <= "
                                + str(lcap[(js, jd, r)])
                            )
                            else:
                              result.append(
                                str(struct.dependencies[(cs, fs, cd, r)])
                                + " >= "
                                + str(lcap[(js, jd, r)])
                                + " * " + self.make_d(cs, fs, js)
                            )

        return result

    def make_obj(self, struct):
        result = "var int: obj = " + "\n\t+ ".join(
            str(struct.importance[(c, i)]) + " * (" + "\n\t+ ".join(self.make_d(c, i, j) for j in struct.nodes) + ")"
            for c in struct.components
            for i in self.flavours[c]
        ) + ";\n"
        return result

    def to_string(self) -> str:
        return "\n".join(self.output)
