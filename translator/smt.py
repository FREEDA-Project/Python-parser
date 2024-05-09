from data.application import Application
from data.infrastructure import Infrastructure
from pysmt.shortcuts import Symbol, And, Plus, serialize, Equals, Int, Implies, Iff
from pysmt.typing import BOOL, INT
from translator.translator import Translator
from translator.intermediate_language import IntermediateLanguage


class SMTTranslator(Translator):
    MAX_BOUND = 1000000

    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate = intermediate_language

    def to_file_string(self) -> str:
        self._set_flavs()
        D, N = self.add_variables()
        constraints = self.add_constraints(D, N)

        fun = self._max_fun(D)
        return constraints.to_smtlib()

    def _transform_requirements(self, name, value):
        if float("inf") == value:
            return SMTTranslator.MAX_BOUND
        return int(value)

    def add_constraints(self, D, N):
        constraints = []
        for component in self.intermediate.comps:
            constraints.extend(
                [
                    D[(component, f, n)] <= 1
                    for f in self.intermediate.flav[component]
                    for n in self.intermediate.nodes
                ]
            )

        for must in self.intermediate.mustComp:
            constraints.append(
                And(
                    N[must] > 0,
                    Equals(
                        Plus(
                            [
                                D[(must, f, n)]
                                for f in self.intermediate.flav[must]
                                for n in self.intermediate.nodes
                            ]
                        ),
                        Int(1),
                    ),
                )
            )

        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    constraints.append(
                        Plus(
                            [
                                D[(component, flav, node)]
                                for node in self.intermediate.nodes
                            ]
                        )
                        <= Plus(
                            [
                                D[(use, flavUse, node)]
                                for flavUse in self.intermediate.flav[use]
                                for node in self.intermediate.nodes
                            ]
                        )
                    )

        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for req, val in self.intermediate.comReq[component][flav].items():
                    for i, node in enumerate(self.intermediate.nodes):
                        val = self._transform_requirements(req, val)
                        if req in self.intermediate.nodeCap[node]:
                            constraints.append(
                                Implies(
                                    Equals(N[component], Int(i)),
                                    Int(val) * D[(component, flav, node)]
                                    <= self._transform_requirements(
                                        req, self.intermediate.nodeCap[node][req]
                                    ),
                                )
                            )

        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    for req, val in self.intermediate.depReq[component][flav].items():
                        if req not in self.intermediate.nodeCap[node]:
                            continue
                        for i1, node1 in enumerate(self.intermediate.nodes):
                            if node1 not in self.intermediate.linkCap:
                                continue
                            for i2, node2 in enumerate(self.intermediate.nodes):
                                if node2 not in self.intermediate.linkCap or req not in self.intermediate.linkCap[node1][node2]:
                                    continue
                                val = self._transform_requirements(req, val)
                                linkCapVal = self._transform_requirements(
                                    req, self.intermediate.linkCap[node1][node2][req]
                                )
                                constraints.append(
                                    Implies(
                                        And(
                                            Equals(N[component], Int(i1)),
                                            Equals(N[use], Int(i2)),
                                        ),
                                        val <= linkCapVal
                                    )
                                )
        return constraints
        
        
    def _max_fun(self,D):
        total_cost = []
        total_cons = []

        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    for req,val in self.intermediate.cost[node].items():
                        val = self._transform_requirements(req, val)
                        if 'carbon' == req:
                            total_cost.append(self.intermediate.comReq[(component,flav,'cpu')] * self.intermediate.cost[node][req]*D[(component,flav,node)])
                        else:
                            total_cost.append(self.intermediate.comReq[(component,flav,req)] * self.intermediate.cost[node][req]*D[(component,flav,node)])

        total_cost = Plus(total_cost)
        total_cons = Plus(total_cons) # add constraints here
        return total_cost
         


    def add_variables(self):
        D = {}
        N = {}
        for component in self.intermediate.comps:
            for flavour in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    D[(component, flavour, node)] = Symbol(
                        f"{component}_{flavour}_{node}", INT
                    )
        for component in self.intermediate.comps:
            N[component] = Plus(
                [
                    D[(component, flavour, node)] * i
                    for flavour in self.intermediate.flav[component]
                    for i, node in enumerate(self.intermediate.nodes)
                ]
            )

        return D, N

    def _set_flavs(self):
        self.flavs = set()
        for val in self.intermediate.flav.values():
            self.flavs = self.flavs.union(val)
