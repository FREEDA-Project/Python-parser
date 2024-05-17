from pulp import (
    LpProblem,
    LpVariable,
    LpMaximize,
    LpStatus,
    lpSum,
    PULP_CBC_CMD,
)
from translator.intermediate_language import IntermediateLanguage
from translator.translator import Translator
from config import DEBUG, CBC_SOLVER_PATH
import time



class PulpTranslator(Translator):
    MAX_BOUND = 1000000

    def __init__(self, intermediate_language: IntermediateLanguage):
        self.intermediate = intermediate_language

    def _gen_problem(self) -> LpProblem:
        self.solver = LpProblem("Solver", LpMaximize)
        D = self.add_variables()
        self.generate_constraints(D)
        self.solver += self.objective(D)
        return self.solver

    def solve(self):
        self.solver = self._gen_problem()
        cplex_solver = PULP_CBC_CMD()
        cplex_solver.path = (
            CBC_SOLVER_PATH
        )


        start_time = time.time()
        self.solver.solve(cplex_solver)
        end_time = time.time()
        execution_time = end_time - start_time
        if LpStatus[self.solver.status] == "Infeasible":
            return None,execution_time

        return list(map(lambda x:str(x),filter(lambda x: x.varValue == 1, self.solver.variables()))),execution_time
        

    def to_file_string(self) -> str:
        raise NotImplementedError()


    def write_to_file(self, file_path: str):
        self._gen_problem().writeMPS(file_path)

    def _transform_requirements(self, name, value):
        if name == "latency":
            return -value 
        return value

    def add_constraint(self, constraint):
        if DEBUG:
            print(constraint)
        if len(self.solver.constraints)==18:
            pass
        if isinstance(constraint, list):
            for c in constraint:
                self.solver += c
        else:
            self.solver += constraint

    def objective(self, D):
        all = []
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    all.append(
                        D[(component, flav, node)]
                        * self.intermediate.flav_to_importance(flav)
                    )

        return lpSum(all)

    def generate_constraints(self, D):
        # 1.3
        for component in self.intermediate.comps:
            self.add_constraint(
                lpSum(
                    [
                        D[(component, flav, node)]
                        for flav in self.intermediate.flav[component]
                        for node in self.intermediate.nodes
                    ]
                )
                <= 1
            )
        # 1.3
        if DEBUG:
            print("-- must component")
        for must in self.intermediate.mustComp:
            # self.add_constraint(N[must] >= 1) # questo può essere tolto
            self.add_constraint(
                lpSum(
                    D[(must, f, n)]
                    for f in self.intermediate.flav[must]
                    for n in self.intermediate.nodes
                )
                == 1
            )

        if DEBUG:
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
        if DEBUG:
            print(" --- component requirements")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for req, val in self.intermediate.comReq[component][flav].items():
                    nodes_with_cap = set(
                        filter(
                            lambda x: x is not None,
                            list(
                                node if req in self.intermediate.nodeCap[node] else None
                                for node in self.intermediate.nodes
                            ),
                        )
                    )
                    # qua imponiamo solo sui nodi che hanno definito la proprietà

                    # forse si può fare di meglio, si possono selezionare i nodi in cui un determinato falvour può andare
                    # e impostare gli altri a zero
                    # volendo si potrebbero direttamente toglierde

                    for node in nodes_with_cap:
                        cap= self._transform_requirements(req,val) 
                        nodeCap= self._transform_requirements(
                               req, self.intermediate.nodeCap[node][req]
                        )
                        if cap>nodeCap:
                            self.add_constraint(D[(component,flav,node)]==0)
                   
        # 1.3.1
        if DEBUG:
            print(" --- comulative requirements")
        for node in self.intermediate.nodes:
            for req, val in self.intermediate.nodeCap[node].items():
                if req not in self.intermediate.CRES_LIST():
                    continue
                component_requirements = []
                for component in self.intermediate.comps:
                    for flav in self.intermediate.flav[component]:
                        if req not in self.intermediate.comReq[component][flav]:
                            continue
                        comp_req = self.intermediate.comReq[component][flav][req]
                        component_requirements.append(
                            self._transform_requirements(req, comp_req)
                            * D[(component, flav, node)]
                        )
                val = self._transform_requirements(req, val)
                self.add_constraint(lpSum(component_requirements) <= val)


        # for node in self.intermediate.nodes:
        #    for req,val in self.intermediate.nodeCap[node].items():
        #        solver += lpSum(
        #            self._transform_requirements(req,self.intermediate.comReq[component][flav][req])*D[(component,flav,node)]
        #            for component in self.intermediate.comps
        #            for flav in self.intermediate.flav[component]
        #        ) <= self._transform_requirements(req,self.intermediate.nodeCap[node][req])

        # 1.3.2
        def get_dep_req(component, use):
            all = []
            if component in self.intermediate.depReq and use in self.intermediate.depReq[component]:
                all = list(self.intermediate.depReq[component][use].item())
            
            if use in self.intermediate.depReq and  component in self.intermediate.depReq[use]:
                all.extend(list(self.intermediate.depReq[use][component].item()))
            
            return all


        if DEBUG:
            print(" --- link requirements")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for uses in self.intermediate.uses[component][flav]:
                    for uses_flav in self.intermediate.flav[uses]:
                        for req,val in self.intermediate.get_dep_req(component,uses):
                            for i, node1 in enumerate(self.intermediate.nodes):
                                for j, node2 in enumerate(self.intermediate.nodes):
                                    if i >= j:
                                        continue
                                    link_cap = self.intermediate.get_link_cap(
                                        node1, node2
                                    )
                                    if link_cap is None or req not in link_cap:
                                        continue

                                    val_link = self._transform_requirements(
                                        req, link_cap[req]
                                    )
                                    val = self._transform_requirements(req,val)
                                    if val >val_link:
                                        self.add_constraint(
                                            D[(component, flav, node1)]
                                            + D[(uses, uses_flav, node2)]
                                            <= 1
                                        )


        total_cost = []
        total_cons = []

        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    for req, val in self.intermediate.cost[node].items():
                        val = self._transform_requirements(req, val)
                        req_comp = "cpu" if req == "carbon" else req
                        if req_comp not in self.intermediate.comReq[component][flav]:
                            continue
                        comp_req = self.intermediate.comReq[component][flav][req_comp]
                        if "carbon" == req:
                            total_cons.append(
                                comp_req * val * D[(component, flav, node)]
                            )
                        else:
                            total_cost.append(
                                comp_req * val * D[(component, flav, node)]
                            )

        total_cost = lpSum(total_cost)
        total_cons = lpSum(total_cons)

        self.add_constraint(total_cons <= self.intermediate.budget_carbon)
        self.add_constraint(total_cost <= self.intermediate.budget_cost)

    def add_variables(self):
        D = {}
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    D[(component, flav, node)] = LpVariable(
                        f"{component}_{flav}_{node}", 0, 1, cat="Binary"
                    )


        return D
