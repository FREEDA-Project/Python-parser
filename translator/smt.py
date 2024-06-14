from pysmt.shortcuts import (
    And,
    Equals,
    Int,
    Ite,
    LE,
    Plus,
    Solver,
    Symbol,
    BOOL
)
from translator.return_enum import ResultEnum
from translator.solver_translator import SolverTranslator

class SMTTranslator(SolverTranslator):

    def to_file_string(self) -> str:
        solver = self.gen_problem()
        return solver.z3.to_smt2()

    def gen_problem(self):
        self.D = {}
        self.constraints = []

        self.add_variables()
        self.generate_contraints()
        return self.constraints

    def _solve(self):
        constraints = self.gen_problem()
        with Solver() as solver:
            solver.add_assertion(And(constraints))
            if solver.solve():
                return ResultEnum.Sat, None
            else:
                return ResultEnum.NonSat, None

    def _get_int_D(self, c, f, n):
        return (Ite(self.D[(c, f, n)], Int(1), Int(0)))

    def _add_at_most_on_flav_and_node(self, component):
        self.add_constraint(
            LE(
                Plus(
                    self._get_int_D(component, f, n)
                    for f in self.intermediate.flav[component]
                    for n in self.intermediate.nodes
                ),
                Int(1),
            )
        )

    def _add_must_component(self, must):
        self.add_constraint(
            Equals(
                Plus(
                    [
                        self._get_int_D(must, f, n)
                        for f in self.intermediate.flav[must]
                        for n in self.intermediate.nodes
                    ]
                ),
                Int(1),
            )
        )

    def _add_deploy_used_component(self, component, flav, use):
        self.add_constraint(
            LE(
                Plus(
                    self._get_int_D(component, flav, node)
                    for node in self.intermediate.nodes
                ),
                Plus(
                    self._get_int_D(use, flavUse, node)
                    for flavUse in self.intermediate.flav[use]
                    for node in self.intermediate.nodes
                ),
            )
        )

    def _add_impossibile_deploy(self, component, flav, node):
        self.add_constraint(Equals(self._get_int_D(component, flav, node),Int(0)))

    def _add_comulative_constaint(self, val, component_requirements):
        self.add_constraint(
            LE(
                Plus(
                    self._get_int_D(c, f, n) * Int(v)
                    for v, (c, f, n) in component_requirements
                ),
                Int(val),
            )
        )

    def _add_impossibile_combination(
        self, component, flav, node, component1, flav1, node1
    ):

        self.add_constraint(
            LE(
                Plus(
                    self._get_int_D(component, flav, node),
                    self._get_int_D(component1, flav1, node1),
                ),
                Int(1),
            )
        )

    def _add_total(self, budget, all_buget):
        self.add_constraint(
            LE(
                Plus(
                    Int(val) * Int(comp_val) * self._get_int_D(component, flav, node)
                    for comp_val, val, (component, flav, node) in all_buget
                ),
                Int(int(budget)),
            )
        )

    def _add_boolean_variabile(self, component, flavour, node):
        self.D[(component, flavour, node)] = Symbol(
            f"{component}_{flavour}_{node}", BOOL
        )


    def _add_objective(self, component, flav, node, val):
        return
