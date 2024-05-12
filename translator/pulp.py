from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, LpStatus,lpSum,PULP_CBC_CMD
from translator.intermediate_language import IntermediateLanguage
from translator.translator import Translator
import subprocess


class PulpTranslator(Translator):

    MAX_BOUND = 1000000
    def __init__(self, intermediate_language: IntermediateLanguage):
        self.intermediate = intermediate_language
    

    def _gen_problem(self) -> LpProblem:
        solver = LpProblem("Solver", LpMaximize)
        D, N = self.add_variables(solver)
        self.add_constraints(D, N, solver)
        result = subprocess.run("which cbc", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("CBC is not installed")

        cplex_solver = PULP_CBC_CMD( result.stdout.strip)
        return solver

    def to_file_string(self) -> str:
        import json
        return json.dumps(self._gen_problem().to_dict())


    def write_to_file(self, file_path: str):
        self._gen_problem().writeMPS(file_path)


    def _transform_requirements(self, name, value):
        if value == float("inf"):
            return PulpTranslator.MAX_BOUND
        return int(value)
    

    def add_constraints(self, D, N, solver):
        # N must be equal to LpSum of flav and nodes of d moltiplied by a constant j
        for component in self.intermediate.comps:
            solver += lpSum([D[(component, flav, node)]*j 
                             for flav in self.intermediate.flav[component]
                             for j,node in enumerate(self.intermediate.nodes)
                             ]) ==  N[component]

        # 1.2
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    solver += D[(component, flav, node)] <= 1

        # 1.3
        for must in self.intermediate.mustComp:
            solver += N[must] >= 1
            solver += (
                lpSum(
                    D[(must, f, n)]
                    for f in self.intermediate.flav[must]
                    for n in self.intermediate.nodes
                )
                == 1 
            ) # TODO: isn't this redundant?
                
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    solver += (
                        lpSum(
                            D[(component, flav, node)]
                            for node in self.intermediate.nodes
                        )
                        <= lpSum(
                            D[(use, flavUse, node)]
                            for flavUse in self.intermediate.flav[use]
                            for node in self.intermediate.nodes
                        )
                    )
        # 1.3.1 
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for req,val in self.intermediate.comReq[component][flav].items():
                    def get_node_cap(node,req):
                        if req in self.intermediate.nodeCap[node]:
                            return self._transform_requirements(req,self.intermediate.nodeCap[node][req])
                        else:
                            print('not set for node',node,req)
                            return PulpTranslator.MAX_BOUND 


                    solver += lpSum(
                        [
                            self._transform_requirements(req, val) * D[(component, flav, node)]
                            for node in self.intermediate.nodes
                        ]
                    )<= lpSum(
                            D[(component, flav, node)]* get_node_cap(node,req)
                            for node in self.intermediate.nodes
                    )
        
        return solver

        def check_com_res(res) :
            return res in self.intermediate.cres
        
        for node in self.intermediate.nodes:
            for req,val in self.intermediate.nodeCap[node].items():
                solver += lpSum(
                    self._transform_requirements(req,self.intermediate.comReq[component][flav][req])*D[(component,flav,node)]
                    for component in self.intermediate.comps
                    for flav in self.intermediate.flav[component]
                ) <= self._transform_requirements(req,self.intermediate.nodeCap[node][req])
        
        K={}
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for uses in self.intermediate.uses[component][flav]:
                    for uses_flav in self.intermediate.flav[uses]:
                        for req,val in self.intermediate.depReq[component][uses]: # qui è importante l'ordine
                            all=[]
                            for i,node1 in enumerate(self.intermediate.nodes):
                                for j,node2 in enumerate(self.intermediate.nodes):
                                    if i <= j :
                                        klen = len(K)
                                        K[klen] = LpVariable(f"N_{klen}", 0, 1, cat="Binary")
                                        all.append(self.intermediate.linkCap[node1][node2][req]*K[klen])
                                        solver+=K[klen]<=D[(component,flav,node1)]
                                        solver+=K[klen]<=D[(uses,uses_flav,node2)]
                                        solver+= K[klen] >= D[(component,flav,node1)] + D[(uses,uses_flav,node2)] -1

                            solver+= self.intermediate.depReq[component][uses][req]<= lpSum(all)
                            
        
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    for req,val in self.intermediate.cost[node].items():
                        val = self._transform_requirements(req, val)
                        if 'carbon' == req:
                            total_cost.append(self.intermediate.comReq[(component,flav,'cpu')] * self.intermediate.cost[node][req]*D[(component,flav,node)])
                        else:
                            total_cost.append(self.intermediate.comReq[(component,flav,req)] * self.intermediate.cost[node][req]*D[(component,flav,node)])

        total_cost = lpSum(total_cost)
        total_cons = lpSum(total_cons) # add constraints here

        solver += total_cons<= self.intermediate.budget_carbon
        solver += total_cost<= self.intermediate.budget_cost




        


    def add_variables(self,solver):
        D = {}
        N = {}
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    D[(component, flav, node)] = LpVariable(
                        f"D_{component}_{flav}_{node}", 0, 1, cat="Binary"
                    )

        for component in self.intermediate.comps:
            N[component] = LpVariable(f"N_{component}", 0, 1, cat="Binary")

        return D, N
