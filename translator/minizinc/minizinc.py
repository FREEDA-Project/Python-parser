from typing import Any, Optional
from translator.intermediate_language import IntermediateLanguage
from translator.translator import Translator






class MiniZinc(Translator):
    cres = ["cpu", "ram", "storage", "bwin", "bwout"]

    def __init__(self, intermediate_language: IntermediateLanguage):
        self.output = ""
        self.intermediate_language = intermediate_language

        self._add_component()
        self._must_components()
        self._add_flavs()
        self._add_nodes()
        self._add_res()
        self._add_flav()
        self._add_uses()
        self._max_bound()
        self._worst_best_bounds()
        self._add_com_req()
        self._link_cap()
        self._node_cap()
        self._cons()
        self._node_cost()
        self._dependency_requirement()
        self._imp()
        self._cons_cost_weight()
        self._budget()

    def _must_components(self):
        self.output += "mustComps = {"
        self.output += ",".join(self.intermediate_language.mustComp)
        self.output += "};\n"


    def _cons(self):
        self.output += "cons = array2d(Nodes0, Res, [\n"
        self._commented_res()
        for i in self.res:
            self.output += "0,"
        self.output += "\n"

        for node_name in self.intermediate_language.nodes:
            for i in self.res:
                if i == "cpu":
                    self.output += str(int(self.intermediate_language.cost[node_name][
                        "carbon"
                    ]))
                else:
                    self.output += "0"
                self.output += ","
            self.output += "% " + node_name + "\n"
        self.output += "]);\n"

    def _add_res(self):
        self.output += "CRes = {"
        cres = []
        for i in self.intermediate_language.res:
            if i.lower() in self.cres:
                cres.append(i)
        self.output += ", ".join(cres)
        self.output += "};\n"

        self.output += "NRes = {"
        nres = []
        for i in self.intermediate_language.res:
            if i.lower() not in self.cres:
                nres.append(i)
        self.output += ", ".join(nres)
        self.output += "};\n"

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
            flav = []
            for val in self.flav:
                if val in  self.intermediate_language.flav[key]  :
                    flav.append(val)
            self.output += "{" + ",".join(flav) + "},"
        self.output += "];\n"

    def _add_uses(self):
        self.output += "Uses = ["
        uses = []
        for key in self.intermediate_language.comps:
            for val in self.flav:
                if val in self.intermediate_language.flav[key]   :
                    uses.append("{" + ",".join(
                        self.intermediate_language.uses[key][val]
                    ) + "}")
        self.output += ",".join(uses)
        self.output += "];\n"

    def _max_bound(self):
        self.output += "MAX_BOUND = 1000000;\n"

    def _add_formatted_res(self, key:str,val) -> str:
            if key == "avail" or key == "availability":
                val = val * 100
            #elif key.lower() == 'ram':
            #    val = val * 10
            
            if val == float("inf"):
                self.output += "MAX_BOUND"
            elif isinstance(val, float):
                self.output += str(int(val))
            else:
                self.output += str(val) 



    def _add_all_resources(self, prop: Any,latency_max=False) -> str:
        for key in self.res:
            if key in prop:
                self._add_formatted_res(key,prop[key])
            else:
                self.output += 'MAX_BOUND' if key=='latency' and latency_max else "0"
            self.output += ","


    def _add_com_req(self):
        self.output += "comReq = array2d(CompFlavs, Res, [\n"
        self._commented_res()
        for component_name in self.intermediate_language.comps:
            for flav_name in self.flav:
                if flav_name in self.intermediate_language.flav[component_name]:
                    if (
                        flav_name not in self.intermediate_language.comReq[component_name]
                        or component_name not in self.intermediate_language.comReq
                    ):
                        self.output += ",".join(self._worst_bounds()) + ","
                    else:
                        flav_val = self.intermediate_language.comReq[component_name][flav_name]
                        self._add_all_resources(flav_val,True)
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
            self._add_all_resources(node_val)
            self.output += "% " + node_name + "\n"

        self.output += "],\n"
        self.output += ");\n"

    def _node_cost(self):
        self.output += "cost = array2d(Nodes0, Res,[\n"
        self._commented_res()
        self.output += ''.join(['0,' for i in self.res]) + " % n0\n"
        for node_name in self.intermediate_language.nodes:
            for res in self.res:
                if res in self.intermediate_language.cost[node_name]:
                    self._add_formatted_res(res,self.intermediate_language.cost[node_name][res])
                else:
                    self.output += "0"
                self.output += ","
            self.output += "% " + node_name + "\n"
        self.output += "]);\n"

    def _budget(self):
        self.output += "costBudget =" + str(int(self.intermediate_language.budget_cost)) + ";\n"
        self.output += "consBudget =" + str(int(self.intermediate_language.budget_carbon)) + ";\n"

    def _link_cap(self):
        self.output += "linkCap = array3d(Nodes0, Nodes0, Res,[\n"
        self.output += "if ni = 0 \\/ nj = 0 then\n"
        self.output += "\tbestBounds[r]\n"
        self.output += "elseif ni = nj then\n"
        self.output += "\tif r = N(availability) then nodeCap[ni,r]\n" #TODO some hardcoded values need to check if they are into the res
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
                        self.output += "\t"
                        if i != 0:
                            self.output += "else"
                        self.output += (
                            "if r = N("
                            + str(cap)
                            + ") then "
                        )
                        self._add_formatted_res(cap,capabilities[cap])

                    self.output += "\t else worstBounds[r]\n"
                    self.output += "endif\n"
                else:
                    self.output += "\tworstBounds[r]\n"
        self.output += "else\n"
        self.output += "\tworstBounds[r]\n"
        self.output += "endif | ni in Nodes0, nj in Nodes0, r in Res\n"
        self.output += "]);\n"

    def _imp(self):
        self.output += "imp = array2d(Comps, Flavs, [\n"
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
        self.output += "depReq = array3d(Comps, Comps, Res,[\n"
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
                    )
                    self._add_formatted_res(res_name,self.intermediate_language.depReq[from_comp][to_comp][res_name])
                    self.output += '\n'
                self.output += "\t else worstBounds[r]\n"
                self.output += "endif\n"
                self.output += "\n"
        self.output += "else\n"
        self.output += "\tworstBounds[r]\n"
        self.output += "endif | ci in Comps, cj in Comps, r in Res\n"
        self.output += "]);\n"

    

    def to_file_string(self) -> str:
        return self.output
