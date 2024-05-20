from pysmt.shortcuts import (
    And,
    Equals,
    Not,
    Int,
    Ite,
    Plus,
    Solver,
    Symbol,
)
from pysmt.typing import BOOL, INT

from config import DEBUG
from data.application import Application
from data.infrastructure import Infrastructure
from translator.intermediate_language import IntermediateLanguage
from translator.solver_translator import SolverTranslator


class SMTTranslator(SolverTranslator):
    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate = intermediate_language

    def to_file_string(self) -> str:
        solver = self.gen_problem() 
        return solver.z3.to_smt2()

    def gen_problem(self):
        self.D = {}
        self.constraints = []
        self.solver =Solver()
        
        self.add_variables()
        self.generate_contraints()
        self.solver.add_assertion(And(self.constraints))
        return self.solver

    def _solve(self):
        solver = self.gen_problem()
        return solver.is_sat() 
    

    def _get_int_D(self, c, f, n):
        return Ite(self.D[(c, f, n)], Int(1), Int(0))

    def _add_at_most_on_flav_and_node(self, component):
        self.add_constraint(
            Plus(
                self._get_int_D(component, f, n)
                for f in self.intermediate.flav[component]
                for n in self.intermediate.nodes
            )
            <= Int(1)
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
            Plus(
                self._get_int_D(component, flav, node)
                for node in self.intermediate.nodes
            )
            <= Plus(
                self._get_int_D(use, flavUse, node)
                for flavUse in self.intermediate.flav[use]
                for node in self.intermediate.nodes
            )
        )


    def _add_impossibile_deploy(self, component, flav, node):
        self.add_constraint(Not(self.D[(component, flav, node)]))

    def _add_comulative_constaint(self, val, component_requirements):
        self.add_constraint(
            Plus(
                self._get_int_D(c, f, n) * v for v, (c, f, n) in component_requirements
            )
            <= Int(val)
        )

    def _add_impossibile_combination(
        self, component, flav, node, component1, flav1, node1
    ):
        self.add_constraint(
            Plus(
                self._get_int_D(component, flav, node),
                self._get_int_D(component1, flav1, node1),
            )
            <= Int(1)
        )

    def _add_total(self, budget, all_buget):
        self.add_constraint(
            Plus(
                val * comp_val * self._get_int_D(component, flav, node)
                for comp_val, val, (component, flav, node) in all_buget
            )
            <= Int(int(budget))
        )

    def _add_boolean_variabile(self, component, flavour, node):
        self.D[(component, flavour, node)] = Symbol(
            f"{component}_{flavour}_{node}", BOOL
        )

    def _add_objective(self, component, flav, node, val):
        pass