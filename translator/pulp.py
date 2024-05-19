
from pulp import (
    PULP_CBC_CMD,
    LpMaximize,
    LpProblem,
    LpStatus,
    LpVariable,
    lpSum,
)

from config import CBC_SOLVER_PATH
from translator.intermediate_language import IntermediateLanguage
from translator.solver_translator import SolverTranslator

class PulpTranslator(SolverTranslator):
    def __init__(self, intermediate_language: IntermediateLanguage):
        self.intermediate = intermediate_language

    def _gen_problem(self) -> LpProblem:
        self.solver = LpProblem("Solver", LpMaximize)
        self.D= {}
        self.constraints = []
        self.add_variables()
        self.generate_contraints()
        for i in self.constraints:
            self.solver += i
        self.objective_f = []
        self.objective()
        self.solver+=lpSum(self.objective_f)
        return self.solver

    def _solve(self):
        self.solver = self._gen_problem()
        cplex_solver = PULP_CBC_CMD(msg=False)
        cplex_solver.path = CBC_SOLVER_PATH
        self.solver.solve(cplex_solver)

        if LpStatus[self.solver.status] == "Infeasible":
            return None
        return list(
            map(
                lambda x: str(x),
                filter(lambda x: x.varValue == 1, self.solver.variables()),
            )
        )

    def to_file_string(self) -> str:
        raise NotImplementedError()

    def write_to_file(self, file_path: str):
        self._gen_problem().writeMPS(file_path)

    def _transform_requirements(self, name, value):
        if name == "latency":
            return -value
        return value

   

    def _add_at_most_on_flav_and_node(self, component):
        self.add_constraint(
            lpSum(
                [
                    self.D[(component, flav, node)]
                    for flav in self.intermediate.flav[component]
                    for node in self.intermediate.nodes
                ]
            )
            <= 1
        )

    def _add_must_component(self, must):
        self.add_constraint(
                lpSum(
                    self.D[(must, f, n)]
                    for f in self.intermediate.flav[must]
                    for n in self.intermediate.nodes
                )
                == 1
        )

    def _add_deploy_used_component(self, component, flav, use):
        self.add_constraint(
            lpSum(
                self.D[(component, flav, node)]
                for node in self.intermediate.nodes
            )
            <= lpSum(
                self.D[(use, flavUse, node)]
                for flavUse in self.intermediate.flav[use]
                for node in self.intermediate.nodes
            )
        )

    def _add_total(self, budget, all_buget):
        self.add_constraint(
            lpSum(
                val * comp_val * self.D[(component, flav, node)]
                for comp_val, val, (component, flav, node) in all_buget
            )
            <= budget
        )

    def _add_impossibile_deploy(self, component, flav, node):
        self.add_constraint(self.D[(component, flav, node)] == False)

    def _add_comulative_constaint(self, val, component_requirements):
        self.add_constraint(
            lpSum(
                self.D[(c, f, n)] * v for v, (c, f, n) in component_requirements
            )
            <= val
        )

    def _add_impossibile_combination(
        self, component, flav, node, component1, flav1, node1
    ):
        self.add_constraint(
            self.D[(component, flav, node)]
            + self.D[(component1, flav1, node1)]
            <= 1
        )

    def _add_boolean_variabile(self,component,flav,node):
        self.D[(component, flav, node)] = LpVariable(
            f"{component}_{flav}_{node}", 0, 1, cat="Binary"
        )

    def _add_objective(self, component, flav, node,val):
        self.objective_f.append(
            val * self.D[(component, flav, node)]
        )