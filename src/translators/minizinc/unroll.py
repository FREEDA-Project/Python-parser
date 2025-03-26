from src.language.intermediate_language import IntermediateStructure
from src.translators.translator import Translator
from .utils import combine_comp_flav

model_output = """
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
];
"""

class MZNUnrollTranslator(Translator): # MZN optimized with unroll format

    def make_d(self, c, i, j) -> str:
        return "D[" + combine_comp_flav(c, i) + ", " + j + "]"

    def __init__(self, struct: IntermediateStructure):
        super(MZNUnrollTranslator, self).__init__(struct)

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

        self.zero_node = "0"
        self.nodes0 = [self.zero_node] + self.structure.nodes

        mx = max(self.structure.worst_bounds.values())
        mn = min(self.structure.best_bounds.values())
        self.wbounds = {
            r : mn if self.structure.resource_minimization[r] else mx
            for r in self.structure.resources
        }

        self.mayUse = {}
        for c in self.structure.components:
            for c_prime in self.structure.components:
                for f_prime in self.flavours[c_prime]:
                    is_used = False
                    for f in self.flavours[c]:
                        if ((c_prime, f_prime) in self.structure.uses) and ((c, f) in self.structure.uses[(c_prime, f_prime)]):
                            is_used = True

                    if is_used:
                        self.mayUse.update({
                            (c, combine_comp_flav(c_prime, f_prime)): 1
                        })

        self.output = []

    def translate(self):
        preamble = "%%% MZN optimized for " + self.structure.app_name + " in " + self.structure.infrastructure_name + " %%%"
        self.output.extend([
            "%" * len(preamble),
            preamble,
            "%" * len(preamble),
            ""
        ])

        self.output.append("enum Comps = {" + ", ".join(self.structure.components) + "};")
        self.output.append("set of Comps: mustComps = {" + ", ".join(self.structure.must_components) + "};")

        self.output.append("enum Flavs = {" + ", ".join(self.structure.flavs) + "};")
        self.output.append("array[Comps] of set of Flavs: Flav = [" + ", ".join(
            "{" + ", ".join(fs) + "}"
            for fs in self.flavours.values()
        ) + "];")

        self.output.append("enum CompFlavs = {" + ", ".join(self.compflavs) + "};")
        self.output.append("enum CRes = {" + ", ".join(self.structure.consumable_resource) + "};")
        self.output.append("enum NRes = {" + ", ".join(self.structure.non_consumable_resource) + "};")
        self.output.append("enum Nodes = {" + ", ".join(self.structure.nodes) + "};")
        self.output.append("set of int: Nodes0 = {" + self.zero_node + "} union Nodes;\n")

        self.output.append("array [{0} union CompFlavs, Nodes0] of var 0..1: D;")
        self.output.append(model_output)
        self.output.append("var int: totCost = " + self.tot_quantity(self.structure.node_cost) + ";")
        self.output.append("var int: totCarb = " + self.tot_quantity(self.structure.node_carb) + ";")
        self.output.append(self.make_obj())
        self.output.append("solve maximize obj;")

        self.constraints = []
        self.constraints.append("totCost <= " + str(self.structure.cost_budget))
        self.constraints.append("totCarb <= " + str(self.structure.carbon_budget))
        self.constraints.extend(self.zero_values())
        self.constraints.extend(self.at_most_one())
        self.constraints.extend(self.must_deploy())
        self.constraints.extend(self.bigger_or_equal())
        self.constraints.extend(self.target_not_in_mustcomps())
        self.constraints.extend(self.sufficient_quantity())
        self.constraints.extend(self.certain_amount())
        self.constraints.extend(self.non_consumable_dependency())

        for c in self.constraints:
            self.output.append("constraint " + c + ";")

        return self

    def make_importance(self):
        result = "array[Comps, Flavs] of int: imp = array2d(Comps, Flavs, [\n"
        result += self.construct_explicit(
            self.structure.importance,
            [
                (self.structure.components, "Comps"),
                (self.structure.flavs, "Flavs")
            ],
            lambda _ : "0"
        )
        return result

    def tot_quantity(self, quantity):
        to_sum = []
        for (c, f, r), v in self.structure.component_requirements.items():
            for n in self.structure.nodes:
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

        for i in self.compflavs:
            result.append("D[" + str(i) + ", " + self.zero_node + "] = 0")

        return result

    def at_most_one(self):
        result = []

        for c in self.structure.components:
            e = []
            for f in self.flavours[c]:
                for j in self.structure.nodes:
                    e.append(self.make_d(c, f, j))
            result.append("\n\t+ ".join(e) + "\n\t<= 1")

        return result

    def must_deploy(self):
        result = []

        for c in self.structure.must_components:
            e = []
            for f in self.flavours[c]:
                for j in self.structure.nodes:
                    e.append(self.make_d(c, f, j))
            result.append("\n\t+ ".join(e) + "\n\t> 0")# /\\ node[" + c + "] > 0")

        return result

    def bigger_or_equal(self):
        result = []

        for c in self.structure.components:
            for i in self.flavours[c]:
                for cu in self.structure.components:
                    for iu in self.flavours[cu]:
                        if (c, i) in self.structure.uses and (cu, iu) in self.structure.uses[(c, i)]:

                            lhs = []
                            for j in self.structure.nodes:
                                lhs.append(self.make_d(c, i, j))

                            rhs = []
                            for k in self.flavours[cu]:
                                if self.structure.importance[(cu, k)] >= self.structure.importance[(cu, iu)]:
                                    for j in self.structure.nodes:
                                        rhs.append(self.make_d(cu, k, j))

                            result.append("\n\t+ ".join(lhs) + "\n\t<=\n\t" + "\n\t+ ".join(rhs))
        return result

    def target_not_in_mustcomps(self):
        result = []

        for c in self.structure.components:
            lhs = []
            if c not in self.structure.must_components:
                for f in self.flavours[c]:
                    for j in self.structure.nodes:
                        lhs.append(self.make_d(c, f, j))

                rhs = []
                for cs in self.structure.components:
                    if c != cs:
                        for fs in self.flavours[cs]:
                            comb = combine_comp_flav(cs, fs)
                            if (c, comb) in self.mayUse and self.mayUse[(c, comb)] == 1:
                                for j in self.structure.nodes:
                                    rhs.append(self.make_d(cs, fs, j))

                result.append(
                    "\n\t+ ".join(lhs) + "\n\t<=\n\t" + "\n\t+ ".join(rhs)
                )
        return result

    def sufficient_quantity(self):
        result = []
        for j in self.structure.nodes:
            for r in self.structure.consumable_resource:
                lhs = []
                if (j, r) in self.structure.node_capabilities:
                    if self.structure.resource_minimization[r]:
                        for c in self.structure.components:
                            for i in self.flavours[c]:
                                if (c, i, r) in self.structure.component_requirements and self.structure.component_requirements[(c, i, r)] != self.wbounds[r]:
                                    lhs.append(
                                        str(self.structure.component_requirements[(c, i, r)])
                                        + " * " + self.make_d(c, i, j)
                                    )
                    else:
                        raise ValueError("Consumable 'maximization' resources unsupported")

                if len(lhs) > 0:
                    result.append("\n\t+ ".join(lhs) + "\n\t<= " + str(self.structure.node_capabilities[(j, r)]))

        return result

    def certain_amount(self):
        ncap = self.structure.node_capabilities | {
            ('0', r) : self.structure.best_bounds[r]
            for r in self.structure.resources
        }

        result = []
        for j in self.nodes0:
            for c in self.structure.components:
                for i in self.flavours[c]:
                    for r in self.structure.non_consumable_resource:
                        if (c, i, r) in self.structure.component_requirements and self.structure.component_requirements[(c, i, r)] != self.wbounds[r]:
                            if self.structure.resource_minimization[r]:
                                result.append(
                                    str(self.structure.component_requirements[(c, i, r)])
                                    + " * "
                                    + self.make_d(c, i, j)
                                    + " <= "
                                    + str(ncap[(j, r)] if (j, r) in ncap else 0)
                                )
                            else:
                                result.append(
                                    str(self.structure.component_requirements[(c, i, r)])
                                    + " >= "
                                    + self.make_d(c, i, j)
                                    + " * "
                                    + str(ncap[(j, r)] if (j, r) in ncap else 0)
                                    + " * "
                                    + self.make_d(c, i, j)
                                )

        return result

    def non_consumable_dependency(self):
        max_rbound = max(self.structure.worst_bounds.values())
        min_rboud = min(self.structure.best_bounds.values())
        lcap = self.structure.link_capacity | {
            ('0', '0', r) : max_rbound if self.structure.resource_minimization[r] else min_rboud
            for r in self.structure.resources
        } | {
            ('0', n, r) : min_rboud if self.structure.resource_minimization[r] else max_rbound
            for r in self.structure.resources
            for n in self.structure.nodes
        } | {
            (n, '0', r) : min_rboud if self.structure.resource_minimization[r] else max_rbound
            for r in self.structure.resources
            for n in self.structure.nodes
        } | {
            (n, n, r) : self.structure.node_capabilities[(n, r)] if (n, r) in self.structure.node_capabilities else 0
            for r in self.structure.resources
            for n in self.structure.nodes
        }

        result = []
        for js in self.nodes0:
          for jd in self.nodes0:
            for r in self.structure.non_consumable_resource:
              if (js, jd, r) in lcap and lcap[(js, jd, r)] != self.wbounds[r]:
                for cs in self.structure.components:
                  for fs in self.flavours[cs]:
                    for cd in self.structure.components:
                      for fd in self.flavours[cd]:
                        if (cd, combine_comp_flav(cs, fs)) in self.mayUse and self.mayUse[(cd, combine_comp_flav(cs, fs))] == 1:
                          if (cs, fs, cd, r) in self.structure.dependencies and self.structure.dependencies[(cs, fs, cd, r)] != self.wbounds[r]:
                            if self.structure.resource_minimization[r]:
                              result.append(
                                str(self.structure.dependencies[(cs, fs, cd, r)])
                                + " * " + self.make_d(cs, fs, js)
                                + " * " + self.make_d(cd, fd, jd)
                                + " <= "
                                + str(lcap[(js, jd, r)])
                            )
                            else:
                              result.append(
                                str(self.structure.dependencies[(cs, fs, cd, r)])
                                + " >= "
                                + str(lcap[(js, jd, r)])
                                + " * " + self.make_d(cs, fs, js)
                                + " * " + self.make_d(cd, fd, jd)
                            )

        return result

    def make_obj(self):
        result = "var int: obj = " + "\n\t+ ".join(
            str(self.structure.importance[(c, i)]) + " * (" + "\n\t\t+ ".join(self.make_d(c, i, j) for j in self.structure.nodes) + ")"
            for c in self.structure.components
            for i in self.flavours[c]
        ) + ";\n"
        return result

    def to_string(self) -> str:
        return "\n".join(self.output)

class MZNUnrollSecondPhaseTranslator(MZNUnrollTranslator):
    def __init__(self, structure):
        super(MZNUnrollSecondPhaseTranslator, self).__init__(structure)

    def make_obj(self):
        result = "var int: obj = " + "\n\t+ ".join([
            self.make_d(c, i, j)
            for (c, i), j in self.structure.old_deployment.items()
        ]) + ";"
        return result

    def translate(self):
        super().translate()

        for (c, f), n in self.structure.constraints["avoid"].items():
            self.output.append(f"constraint {self.make_d(c, f, n)} = 0;")
        for (c1, f1), (c2, f2) in self.structure.constraints["affinity"].items():
            for j in self.structure.nodes:
                self.output.append(
                    f"constraint {self.make_d(c1, f1, j)} * {self.make_d(c2, f2, j)} = 1;"
                )
        for (c1, f1), (c2, f2) in self.structure.constraints["antiaffinity"].items():
            for j in self.structure.nodes:
                self.output.append(
                    f"constraint {self.make_d(c1, f1, j)} * {self.make_d(c2, f2, j)} = 0;"
                )

        return self
