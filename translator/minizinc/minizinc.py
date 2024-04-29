from typing import Any
from translator.intermediate_language import IntermediateLanguage
from translator.translator import Translator


class MiniZinc(Translator):
    cres = ["cpu", "ram", "storage", "bwin", "bwout"]

    def __init__(self, intermediate_language: IntermediateLanguage):
        self.output = ""
        self.intermediate_language = intermediate_language

        self._add_component()
        self._add_nodes()
        self._add_res()
        self._add_flavs()
        self._add_flav()
        self._add_uses()
        self._max_bound()
        self._worst_best_bounds()
        self._add_com_req()
        self._link_cap()
        self._node_cap()
        self._node_cost()
        self._dependency_requirement()
        self._imp()
        self._cons()

    def _cons(self):
        self.output += "cons = array2d(Nodes0, Res, [\n"
        self._commented_res()
        for i in self.res:
            self.output += "0,"
        self.output += "\n"

        for node_name in self.intermediate_language.nodes:
            for i in self.res:
                if i == "cpu":
                    self.output += str(self.intermediate_language.cost[node_name][
                        "carbon"
                    ])
                else:
                    self.output += "0,"
            self.output += "% " + node_name + "\n"
        self.output += "]);\n"

    def _add_res(self):
        output = "CRes = {"
        cres = []
        for i in self.intermediate_language.res:
            if i.lower() in self.cres:
                cres.append(i)
        output += ", ".join(cres)
        output += "};"

        output += "NRes = {"
        nres = []
        for i in self.intermediate_language.res:
            if i.lower() not in self.cres:
                nres.append(i)
        output += ", ".join(nres)
        output += "};"

        self.res = cres + nres

    def _add_component(self):
        self.output += "Comps = {"
        self.output += ",".join(self.intermediate_language.comps)
        self.output += "};\n"

    def _add_nodes(self):
        self.output += "Nodes = {"
        self.output += ",".join(self.intermediate_language.nodes)
        self.output += "};\n"

    def _add_flavs(self):
        self.output += "Flavs = {"
        set_flav = set()
        for val in self.intermediate_language.flav.values():
            set_flav = set_flav.union(val)
        self.output += ",".join(set_flav)
        self.flav = set_flav
        self.output += "};\n"

    def _add_flav(self):
        self.output += "Flav = ["
        for key in self.intermediate_language.comps:
            self.output += "{" + ",".join(self.intermediate_language.flav[key]) + "},"
        self.output += "];\n"

    def _add_uses(self):
        self.output += "Uses = ["
        uses = []
        for key in self.intermediate_language.comps:
            for name, val in self.intermediate_language.uses[key].items():
                uses.append("{" + ",".join(val) + "}")
        self.output += ",".join(uses)
        self.output += "];\n"

    def _max_bound(self):
        self.output += "MAX_BOUND = 1000000;\n"

    def _add_capability_or_requirement(self, prop: Any) -> str:
        print(prop)
        prop = {k.lower(): v for k, v in prop.items()}
        for key in self.res:
            if key == "latency":
                self.output += "MAX_BOUND,"
            elif key in prop:
                if prop[key] == float("inf"):
                    self.output += "MAX_BOUND,"
                else:
                    self.output += str(prop[key]) + ","
            else:
                self.output += "0,"

    def _add_com_req(self):
        self.output += "comReq = array2d(CompFlavs, Res, [\n"
        self._commented_res()
        for component_name in self.intermediate_language.comps:
            for flav_name in self.intermediate_language.flav[component_name]:
                if (
                    flav_name not in self.intermediate_language.comReq[component_name]
                    or component_name not in self.intermediate_language.comReq
                ):
                    self.output += ",".join(self._worst_bounds()) + ","
                else:
                    comp_val = self.intermediate_language.comReq[component_name]
                    flav_val = comp_val[flav_name]
                    self._add_capability_or_requirement(flav_val)
                self.output += "% " + component_name + "," + flav_name
                self.output += "\n"
        self.output += "]);\n"

    @classmethod
    def from_intermediate_language(
        cls, intermediate_language: IntermediateLanguage
    ) -> "MiniZinc":
        return cls(intermediate_language)

    def _worst_bounds(self) -> list[str]:
        worstBounds = []
        for name in self.res:
            if name == "latency":
                worstBounds.append("MAX_BOUND")
            else:
                worstBounds.append("0")
        return worstBounds

    def _worst_best_bounds(self):
        self.output += "%"
        for name in self.res:
            self.output += name + ","
        self.output += "\n"
        self.output += "worstBounds = ["
        self.output += ",".join(self._worst_bounds())
        self.output += "];\n"
        self.output += "bestBounds = [MAX_BOUND - i | i in worstBounds];\n"

    def _commented_res(self):
        self.output += "%"
        for name in self.res:
            self.output += name + ","
        self.output += "\n"

    def _node_cap(self):
        self.output += "nodeCap = array2d(Nodes0, Res,\n"
        self._commented_res()
        self.output += "[ bestBounds[r] | r in Res] ++ "
        self.output += "[\n"
        for node_name in self.intermediate_language.nodes:
            node_val = self.intermediate_language.nodeCap[node_name]
            self._add_capability_or_requirement(node_val)
            self.output += "% " + node_name + "\n"

        self.output += "],\n"
        self.output += ");\n"

    def _node_cost(self):
        self.output += "nodeCost = array1d(Nodes0, Res,[\n"
        self._commented_res()
        for node_name in self.intermediate_language.nodes:
            for res in self.res:
                if res in self.intermediate_language.cost[node_name]:
                    self.output += (
                        str(self.intermediate_language.cost[node_name][res]) + ","
                    )
                else:
                    self.output += "0,"
            self.output += "% " + node_name + "\n"
        self.output += "]);\n"

    def _budget(self):
        self.output += "costBudget =" + self.intermediate_language.budget_carbon + "\n"
        self.output += "carbonBudget =" + self.intermediate_language.budget_cost + "\n"

    def _link_cap(self):
        self.output += "linkCap = array3d(Nodes0, Nodes0, Res,[\n"
        self.output += "if ni = 0 \\/ nj = 0 then\n"
        self.output += "\tbestBounds[r]\n"
        self.output += "elseif ni = nj then\n"
        self.output += "\tif r = N(avail) then nodeCap[ni,r]\n"
        self.output += "\telseif r = N(latency) then 0\n"
        self.output += "\telse worstBounds[r]\n"
        self.output += "endif\n"
        for node_name in self.intermediate_language.linkCap:
            for node_name2 in self.intermediate_language.linkCap[node_name]:
                self.output += (
                    "elseif ni = " + node_name + " \\/ nj = " + node_name2 + " then\n"
                )
                capabilities = self.intermediate_language.linkCap[node_name][node_name2]
                if len(capabilities) != 0:
                    for i, cap in enumerate(capabilities):
                        if i == 0:
                            self.output += (
                                "\t if r = N("
                                + str(cap)
                                + ") then "
                                + str(capabilities[cap])
                                + "\n"
                            )
                        else:
                            self.output += (
                                "\telseif r = N("
                                + str(cap)
                                + ") then "
                                + str(capabilities[cap])
                                + "\n"
                            )

                    self.output += "\t else worstBounds[r]\n"
                    self.output += "endif\n"
                else:
                    self.output += "\tworstBounds[r]\n"
        self.output += "else\n"
        self.output += "\tworstBounds[r]\n"
        self.output += "endif | ni in Nodes0, nj in Nodes0, r in Res\n"
        self.output += "]);\n"

    def _imp(self):
        self.output += "imp = array2d(Comp, Flavs, [\n"
        for comp in self.intermediate_language.comps:
            for flav in self.flav:
                if flav == "tiny":
                    self.output += "1,"
                elif flav == "medium":
                    self.output += "2,"
                elif flav == "large":
                    self.output += "3,"
                else:
                    self.output += "0,"
            self.output += "% " + comp + "\n"
        self.output += "]);\n"

    def _cons_cost_weight(self):
        self.output += "costWeight = 0;\n"
        self.output += "consWeight = 1;\n"

    def _dependency_requirement(self):
        self.output += "depReq = array3d(Comp, Comp, Res,[\n"
        first = True
        for from_comp in self.intermediate_language.depReq:
            for to_comp in self.intermediate_language.depReq[from_comp]:
                if first:
                    first = False
                else:
                    self.output += "else"
                self.output += (
                    "if ci = " + from_comp + " \\/ cj = " + to_comp + " then\n"
                )
                for i, res_name in enumerate(
                    self.intermediate_language.depReq[from_comp][to_comp]
                ):
                    self.output += "\t"
                    if i != 0:
                        self.output += "else"
                    self.output += (
                        "if r = N("
                        + res_name
                        + ") then "
                        + str(
                            self.intermediate_language.depReq[from_comp][to_comp][
                                res_name
                            ]
                        )
                        + "\n"
                    )
                self.output += "\t else worstBounds[r]\n"
                self.output += "\n"
        self.output += "else\n"
        self.output += "\tworstBounds[r]\n"
        self.output += "endif | ci in Comp, cj in Comp, r in Res\n"
        self.output += "]);\n"

    def to_file_string(self) -> str:
        return self.output
