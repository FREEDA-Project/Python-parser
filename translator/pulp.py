from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, LpStatus,lpSum,PULP_CBC_CMD
from translator.intermediate_language import IntermediateLanguage
from translator.translator import Translator
import subprocess
from config import DEBUG


class PulpTranslator(Translator):

    MAX_BOUND = 1000000
    def __init__(self, intermediate_language: IntermediateLanguage):
        self.intermediate = intermediate_language
    

    def _gen_problem(self) -> LpProblem:
        self.solver = LpProblem("Solver", LpMaximize)
        D = self.add_variables(self.solver)
        self.generate_constraints(D )
        result = subprocess.run("which cbc", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("CBC is not installed")

        cplex_solver = PULP_CBC_CMD( result.stdout.strip)
        return self.solver

    def to_file_string(self) -> str:
        import json
        return json.dumps(self._gen_problem().to_dict())


    def write_to_file(self, file_path: str):
        self._gen_problem().writeMPS(file_path)


    def _transform_requirements(self, name, value):
        return value
    

    def add_constraint(self,constraint):
        if DEBUG:
            print(constraint)
        if isinstance(constraint, list):
            for c in constraint:
                self.solver+= c
        else:
            self.solver += constraint


    def generate_constraints(self, D ):
        # N must be equal to LpSum of flav and nodes of d moltiplied by a constant j
        #for component in self.intermediate.comps:
        #    self.add_constraint(lpSum([D[(component, flav, node)]*(j+1) 
        #                     for flav in self.intermediate.flav[component]
        #                     for j,node in enumerate(self.intermediate.nodes)
        #                     ]) ==  N[component])

        # 1.3
        for component in self.intermediate.comps:
            self.add_constraint(lpSum([D[(component, flav, node)]
                for flav in self.intermediate.flav[component]
                for node in self.intermediate.nodes]) <= 1)
        # 1.3
        print('-- must component')
        for must in self.intermediate.mustComp:
            #self.add_constraint(N[must] >= 1) # questo può essere tolto
            self.add_constraint(
                lpSum(
                    D[(must, f, n)]
                    for f in self.intermediate.flav[must]
                    for n in self.intermediate.nodes
                )
                == 1 
            ) 
                
        print(" --- deploy used components ")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    self.add_constraint(
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
        print(" --- component requirements")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for req,val in self.intermediate.comReq[component][flav].items():

                    nodes_with_cap = set(filter(lambda x:x is not  None,
                            list(node if req in self.intermediate.nodeCap[node] else None
                            for node in self.intermediate.nodes)
                    ))
                    # qua imponiamo solo sui nodi che hanno definito la proprietà

                    self.add_constraint(lpSum(
                    
                            self._transform_requirements(req, val) * D[(component, flav, node)]
                            for node in nodes_with_cap
                    )<= lpSum(
                            D[(component, flav, node)]* 
                            self._transform_requirements(req,self.intermediate.nodeCap[node][req])
                            for node in nodes_with_cap
                    ))
        
        # 1.3.1
        print(" --- comulative requirements")

        for node in self.intermediate.nodes:
            for req, val in self.intermediate.nodeCap[node].items():
                if req not in self.intermediate.res:
                    continue
                component_requirements = []
                for component in self.intermediate.comps:
                    for flav in self.intermediate.flav[component]:
                        if req not in self.intermediate.comReq[component][flav]:
                            continue
                        cr = self._transform_requirements(req, self.intermediate.comReq[component][flav][req])
                        component_requirements.append( cr* D[(component, flav, node)])
                val = self._transform_requirements(req, val)
                self.add_constraint(lpSum(component_requirements) <= val)

        
        #for node in self.intermediate.nodes:
        #    for req,val in self.intermediate.nodeCap[node].items():
        #        solver += lpSum(
        #            self._transform_requirements(req,self.intermediate.comReq[component][flav][req])*D[(component,flav,node)]
        #            for component in self.intermediate.comps
        #            for flav in self.intermediate.flav[component]
        #        ) <= self._transform_requirements(req,self.intermediate.nodeCap[node][req])

        # 1.3.2


        print(" --- link requirements")
        K={}
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for uses in self.intermediate.uses[component][flav]:
                    for uses_flav in self.intermediate.flav[uses]:
                        for req,val in self.intermediate.depReq[component][uses].items(): # qui è importante l'ordine
                            all=[]
                            for i,node1 in enumerate(self.intermediate.nodes):
                                for j,node2 in enumerate(self.intermediate.nodes):
                                    if i>=j:
                                        continue
                                    link_cap = self.intermediate.get_link_cap(node1,node2)
                                    if link_cap is None or req not in link_cap:
                                        continue

                                    val_link = self._transform_requirements(req,link_cap[req])
                                    klen = len(K)
                                    K[klen] = LpVariable(f"K_{klen}", 0, 1, cat="Binary")
                                    all.append(val_link*K[klen])
                                    solver+= K[klen]<=D[(component,flav,node1)]
                                    solver+= K[klen]<=D[(uses,uses_flav,node2)]
                                    solver+= K[klen] >= D[(component,flav,node1)] + D[(uses,uses_flav,node2)] -1

                            val = self._transform_requirements(req,val)
                            solver+= val <= lpSum(all)
                            
        
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
        #N = {}
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    D[(component, flav, node)] = LpVariable(
                        f"D_{component}_{flav}_{node}", 0, 1, cat="Binary"
                    )

        #for component in self.intermediate.comps:
        #    N[component] = LpVariable(f"N_{component}", 0, 1, cat="Binary")

        return D
