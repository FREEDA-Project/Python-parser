from typing import Any
from translator.intermidiate_language import IntermediateLanguage
from translator.translator import Translator

class MiniZinkParser(Translator):

    cres = ["cpu", "ram", "storage", "bwin", "bwout"]


    def __init__(self, intermediate_language:IntermediateLanguage):
        self.output = ""
        self.intermediate_language=intermediate_language

        self._add_component()
        self._add_nodes() 
        self._add_flavs()
        self._add_flav()
        self._add_uses()
        self._max_bound()
        self._add_res()

    def _add_res(self):
        output = "CRes = {"        
        cres= []
        for i in self.intermediate_language.res:
            if i.lower() in self.cres:
                cres.append(i)
        output = output + ",".join(cres)
        output+="};"

        output+="NRes = {"
        nres= []
        for i in self.intermediate_language.res:
            if i.lower() not in self.cres:
                nres.append(i)
        output = output + ",".join(nres)
        output+="};"

        self.res = cres + nres

    def _add_component(self):
        self.output= "Comps = {"
        self.output = self.output + ",".join(self.intermediate_language.comps)
        self.output+="};"
    
    def _add_nodes(self):
        self.output= "Nodes = {"
        self.output = self.output + ",".join(self.intermediate_language.nodes)
        self.output+="};"
    
    def _add_flavs(self):
        self.output= "Flavs = {"
        set_flav = set()
        for val in self.intermediate_language.flav.items():
            set_flav = set_flav.union(val)
        self.output = self.output + ",".join(set_flav)
        self.output+="};"
    
    def _add_flav(self):
        self.output= "Flav = ["
        for key,_ in self.intermediate_language.comps.items():
            self.output = self.output + "{" + ",".join(
                self.intermediate_language.flav[key]
            ) + "},"
        self.output+="];" 
    
    def _add_uses(self):
        self.output= "Uses = ["
        uses = []
        for key in self.intermediate_language.comps:
            for name,val in self.intermediate_language.uses[key].items():
                uses.append("{" + ",".join(val) + "}")
        self.output+= ','.join(uses)
        self.output+="];"
    
    def _max_bound(self):
        self.output += "MAX_BOUND = 1000000;"
    
    def _add_capability_or_requirement(self, prop: Any) -> str:
        for key in self.res:
            if key in prop.name.lower():
                if prop.value==float('inf'):
                    self.output+="MAX_BOUND,"
                else:
                    self.output+=str(prop.value)+","
            elif prop.name.lower() == "latency":
                self.output+="MAX_BOUND,"
            else:
                self.output+="0,"
    
    def _add_com_req(self):
        self.output = "comReq = array2d(CompFlavs, Res, ["
        for comp_name,comp_val in self.intermediate_language.comReq.items():
            for flav_name,flav_val in comp_val.items():
                self._add_capability_or_requirement(flav_val)
        self.output+="]);" 
    @classmethod
    def from_intermediate_language(cls, intermediate_language:IntermediateLanguage) -> "MiniZinkParser":
        return cls(intermediate_language)

    def to_file_string(self) -> str:
        return self.minizinc_string
    
"""
 
 Comps = {frontend, backend, database};
 
 mustComps = {frontend};
 
 Flavs = {tiny, medium, large};
 
 Nodes = {n1, n2, n3};
 
 CRes = {CPU, RAM, storage, bwIn, bwOut};
 
 NRes = {ssl, fwall, encr, avail, latency};
 
 Flav = [
   {medium, large}, {tiny, medium, large}, {large}
 ];
 
 Uses = [
   {backend}, {backend}, {}, {database}, {database}, {}
 ];
 
 MAX_BOUND = 1000000;
 % No value for r can be worse than worstBounds(r).
 worstBounds = [0, 0, 0, 0, 0, 0, 0, 0, 0, MAX_BOUND];
 % No value for r can be better than bestBounds(r).
 bestBounds = [MAX_BOUND - i | i in worstBounds];
 
 comReq = array2d(CompFlavs, Res, [
 % CPU, 10*RAM, storage, bwIn, bwOut,  ssl, fwall, encr, 100*avail, latency for:
   1,  5, 0, 1000, 1000, 1, 1, 0, 98, MAX_BOUND, % frontend,medium (not soft)
   2, 10, 0, 1000, 1000, 1, 1, 0, 98, MAX_BOUND, % frontend,large (no soft)
   1, 20, 0, 1000,  600, 1, 0, 0, 98, MAX_BOUND, % backend,tiny
   2, 40, 0, 1000,  600, 1, 0, 0, 98, MAX_BOUND, % backend,medium
   4, 80, 0, 1000,  600, 1, 0, 0, 98, MAX_BOUND, % backend,large
   1, 80, 512, 200, 200, 1, 0, 1, 99, MAX_BOUND, % database,large
 ]);
 
 nodeCap = array2d(Nodes0, Res,
 % CPU, 10*RAM, storage, bwIn, bwOut,  ssl, fwall, encr, 100*avail, latency
   [bestBounds[r] | r in Res] ++ [ % No node
   2,    80,  128, 100,   200, 1, 1, 1, 80, 0, % n1
   4,   320,  512, 100,   200, 1, 0, 1, 80, 0, % n2
   32, 5120, 1024, 3000, 3000, 1, 1, 1, 99, 0] % n3
 ); 
"""
            