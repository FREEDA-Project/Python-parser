from data.application import Application
from data.infrastructure import Infrastructure
from z3 import Symbol, And, Sum,  Int, Implies, Or,Optimize
from translator.translator import Translator
from translator.intermediate_language import IntermediateLanguage
from config import DEBUG


class Z3Translator(Translator):
    MAX_BOUND = 1_000_000

    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate = intermediate_language

    def to_file_string(self) -> str:
        self._set_flavs()
        D, N = self.add_variables()
        constraints = self.generate_constraints(D, N)

        opt = Optimize()
        opt.add(constraints)
        opt.maximize(self.objective(D,N))
        opt.check()
        model = opt.model()
        print(model)
        return model

    def objective(self,D,N):
        all = []
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    all.append(D[(component,flav,node)]*self.intermediate.flav_to_importance(flav))
        
        return Sum(all)

    def _transform_requirements(self, name, value):
        return value

    def add_constraints(self,constraint):
        # check if constarint is a list
        if DEBUG:
            print(constraint)
        if isinstance(constraint, list):
            self.constraints.extend(constraint)
        else:
            self.constraints.append(constraint) 

    def generate_constraints(self, D, N):
        self.constraints = []
        # 1.2
        print(" --- deploy at most one flavour of a component on a node")
        for component in self.intermediate.comps:
            self.add_constraints(
                    Sum([
                        D[(component, f, n)] 
                        for f in self.intermediate.flav[component]
                        for n in self.intermediate.nodes
                    ])<= Int(1)
           ) 
        # 1.3

        print(" --- must component")
        for must in self.intermediate.mustComp:
            self.add_constraints(
                And(
                    N[must] > 0,
                        Sum([
                            D[(must, f, n)]
                            for f in self.intermediate.flav[must]
                            for n in self.intermediate.nodes
                        ]) == Int(1)
                )
            )
        
        print(" --- deploy used components ")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    self.add_constraints(
                        Sum(
                            [
                                D[(component, flav, node)]
                                for node in self.intermediate.nodes
                            ]
                        )
                        >= Sum(
                            [
                                D[(use, flavUse, node)]
                                for flavUse in self.intermediate.flav[use]
                                for node in self.intermediate.nodes
                            ]
                        )
                    )

        # 1.3.1
        print(" --- component requirements")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for req, val in self.intermediate.comReq[component][flav].items():
                    for i, node in enumerate(self.intermediate.nodes):
                        val = self._transform_requirements(req, val)
                        if req in self.intermediate.nodeCap[node]:
                            print(" --- ", req, val, node)
                            self.add_constraints(
                                Implies(
                                    N[component] == Int(i+1),
                                    Int(val) * D[(component, flav, node)]
                                    <= self._transform_requirements(
                                        req, self.intermediate.nodeCap[node][req]
                                    ),
                                )
                            )
        
        # 1.3.1
        print(" --- comulative requirements")

        for node in self.intermediate.nodes:
            for req, val in self.intermediate.nodeCap[node].items():
                if req not in self.intermediate.cres:
                    continue
                component_requirements = []
                for component in self.intermediate.comps:
                    for flav in self.intermediate.flav[component]:
                        if req not in self.intermediate.comReq[component][flav]:
                            continue
                        comp_req = self.intermediate.comReq[component][flav][req]
                        component_requirements.append(self._transform_requirements(req, comp_req) * D[(component, flav, node)])
                val = self._transform_requirements(req, val)
                self.add_constraints(Sum(component_requirements) <= val)

        # 1.3.2
        print(" --- link requirements")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    for req, val in self.intermediate.depReq[component][use].items():
                        val = self._transform_requirements(req, val)
                        possible_nodes = []
                        for i1, node1 in enumerate(self.intermediate.nodes):
                            for i2, node2 in enumerate(self.intermediate.nodes):
                                if i1 >= i2:
                                    continue
                                link_cap = self.intermediate.get_link_cap(node1,node2)
                                if link_cap is None or req not in link_cap:
                                    # TODO: nell'esempio sono tutti definiti però nel caso reale non si sa
                                    continue
                                linkCapVal = self._transform_requirements(req, link_cap[req])
                                if val <= linkCapVal: # per alcuni deve essere maggiore
                                    print(i1,i2)
                                    possible_nodes.append(
                                        And(
                                            N[component]== Int(i1+1),
                                            N[use]== Int(i2+1),
                                        )
                                    )

                        self.add_constraints(
                            Implies(
                                And(
                                    N[component] > 0,
                                    N[use] > 0,
                                ),
                                Or(possible_nodes),
                            )
                        )

        
        # 1.3.3
        print(" --- budget requirements") 
        total_cost = []
        total_cons = []

        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    for req,val in self.intermediate.cost[node].items():
                        val = self._transform_requirements(req, val)
                        req_comp = 'cpu' if req == 'carbon' else req
                        if req_comp not in self.intermediate.comReq[component][flav]:
                            continue
                        comp_req = self.intermediate.comReq[component][flav][req_comp]
                        if 'carbon' == req:
                            total_cons.append(comp_req * val*D[(component,flav,node)])
                        else:
                            total_cost.append(comp_req* val*D[(component,flav,node)])

        total_cost = Sum(total_cost)
        total_cons = Sum(total_cons) # add constraints here

        self.add_constraints(total_cons <= self.intermediate.budget_carbon)
        self.add_constraints(total_cost <= self.intermediate.budget_cost)

        return And(self.constraints)
         
    

    def add_variables(self):
        D = {}
        N = {}
        for component in self.intermediate.comps:
            for flavour in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    D[(component, flavour, node)] = Int(
                        f"{component}_{flavour}_{node}"
                    )
        for component in self.intermediate.comps:
            N[component] = Sum(
                [
                    D[(component, flavour, node)] * (i + 1)
                    for flavour in self.intermediate.flav[component]
                    for i, node in enumerate(self.intermediate.nodes)
                ]
            )

        return D, N

    def _set_flavs(self):
        self.flavs = set()
        for val in self.intermediate.flav.values():
            self.flavs = self.flavs.union(val)
