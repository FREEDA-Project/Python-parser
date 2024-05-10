from pulp import LpProblem, LpVariable, LpMaximize, LpMinimize, LpStatus, value,LpSum
from translator.intermediate_language import IntermediateLanguage
from translator.translator import Translator


class PlupTranslator(Translator):

    MAX_BOUND = 1000000
    def __init__(self, intermediate_language: IntermediateLanguage):
        self.intermediate = intermediate_language

    def to_file_string(self) -> str:
        solver = LpProblem("Solver", LpMaximize)
        D, N = self.add_variables(solver)
        self.add_constraints(D, N, solver)


    def _transform_requirements(self, name, value):
        if value == float("inf"):
            return PlupTranslator.MAX_BOUND
        return int(value)
    

    def add_constraints(self, D, N, solver):
        # add N constraint

        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    solver += D[(component, flav, node)] <= 1

        # N must be equal to LpSum of flav and nodes of d moltiplied by a constant j
        for component in self.intermediate.comps:
            solver += LpSum(
                [
                    D[(component, flav, node)] <= j * N[component]
                    for flav in self.intermediate.flav[component]
                    for j, node in enumerate(self.intermediate.nodes)
                ]
            )

        for must in self.intermediate.mustComp:
            solver += N[must] >= 1
            solver += (
                LpSum(
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
                        LpSum(
                            D[(component, flav, node)]
                            for node in self.intermediate.nodes
                        )
                        <= LpSum(
                            D[(use, flavUse, node)]
                            for flavUse in self.intermediate.flav[use]
                            for node in self.intermediate.nodes
                        )
                    )
        
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for req,val in self.intermediate.comReq[component][flav].items():
                    solver += LpSum(
                        [
                            self._transform_requirements(req, val) * D[(component, flav, node)]
                            for node in self.intermediate.nodes
                        ]
                    )<= LpSum(
                            self._transform_requirements(req, val) * D[(use, flav, node)]
                            for node in self.intermediate.nodes
                    )

    def add_variables(self):
        D = {}
        N = {}
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    D[(component, flav, node)] = LpVariable(
                        f"D_{component}_{flav}_{node}", 0, 1, cat="Binary"
                    )

        for must in self.intermediate.mustComp:
            N[must] = LpVariable(f"N_{must}", 0, 1, cat="Binary")

        return D, N
