from src.language.intermediate_language import IntermediateStructure
from src.translators.translator import Translator
from .utils import construct_explicit, combine_comp_flav

class DZNTranslator(Translator):
    def __init__(self, structure: IntermediateStructure):
        super(DZNTranslator, self).__init__(structure)

        self.comps_initial = "Comps = {"
        self.mustcomps_initial = "mustComps = {"
        self.flavs_initial = "Flavs = {"
        self.flav_initial = "Flav = ["
        self.importance_initial = "imp = array2d(Comps, Flavs, [\n"
        self.energy_initial = "energy = ["
        self.energy_dependency_initial = "energy_dependency = array3d(Comps, Flavs, Comps, ["
        self.uses_initial = "Uses = array2d(CompFlavs, CompFlavs, ["
        self.mayUse_initial = "mayUse = array2d(Comps, CompFlavs, ["
        self.cres_initial = "CRes = {"
        self.nres_initial = "NRes = {"
        self.max_bound_initial = "MAX_RBOUNDS = "
        self.min_bound_initial = "MIN_RBOUNDS = "
        self.worst_bound_initial = "worstBounds = [\n"
        self.best_bound_initial = "bestBounds = [\n"
        self.comReq_initial = "comReq = array2d(CompFlavs, Res, [\n"
        self.nodes_initial = "Nodes = {"
        self.nodeCap_initial = "nodeCap = array2d(Nodes0, Res,\n"
        self.depReq_initiale = "depReq = array4d(Comps, Flavs, Comps, Res, [\n"
        self.linkCap_initial = "linkCap = array3d(Nodes0, Nodes0, Res, [\n"
        self.cost_initial = "cost = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node\n"
        self.carb_initial = "carb = array1d(Nodes0, [0] ++ [ % No node\n\t"
        self.costbudget_initial = "costBudget = "
        self.carbbudget_initial = "carbBudget = "

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

        self.output = []

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
