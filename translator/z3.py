from z3 import (
    Bool,
    Optimize,
    Sum,
    sat,
    Not
)
from translator.return_enum import ResultEnum
from config import DEBUG
from translator.intermediate_language import IntermediateLanguage
from translator.solver_translator import SolverTranslator

class Z3Translator(SolverTranslator):

    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate = intermediate_language

    def to_file_string(self) -> str:
        opt = self.gen_problem()
        return str(opt)

    def gen_problem(self):
        self.D = {}
        self.objective_f = []
        self.constraints = []
        self.add_variables()
        self.generate_contraints()
        opt = Optimize()
        self.objective()
        opt.maximize(Sum(self.objective_f))

        opt.add(self.constraints)
        return opt

    def _solve(self):
        opt = self.gen_problem()
        if opt.check() == sat:
            model = opt.model()
            return ResultEnum.Sat, [str(k) for k in model if model[k]]
        else:
            return ResultEnum.NonSat, None

    def _add_at_most_on_flav_and_node(self, component):
        self.add_constraint(Sum([
            self.D[(component, f, n)]
            for f in self.intermediate.flav[component]
            for n in self.intermediate.nodes
        ]) <= 1)

    def _add_must_component(self, must):
        self.add_constraint(Sum([
            self.D[(must, f, n)]
            for f in self.intermediate.flav[must]
            for n in self.intermediate.nodes
        ]) == 1)

    def _add_deploy_used_component(self, component, flav, use):
        self.add_constraint(
            Sum([
                self.D[(component, flav, node)]
                for node in self.intermediate.nodes
            ]) <= Sum([
                self.D[(use, flavUse, node)]
                for flavUse in self.intermediate.flav[use]
                for node in self.intermediate.nodes
            ])
        )

    def _add_impossibile_deploy(self, component, flav, node):
        self.add_constraint(Not(self.D[(component, flav, node)]))

    def _add_comulative_constaint(self, val, component_requirements):
        self.add_constraint(Sum([
            self.D[(c, f, n)] * v
            for v, (c, f, n) in component_requirements
        ]) <= val)

    def _add_impossibile_combination(
        self,
        component,
        flav,
        node,
        component1,
        flav1,
        node1
    ):
        self.add_constraint(Sum(
            self.D[(component, flav, node)],
            self.D[(component1, flav1, node1)]
        ) <= 1)

    def _add_total(self, budget, all_buget):
        self.add_constraint(Sum([
            val * comp_val * self.D[(component, flav, node)]
            for comp_val, val, (component, flav, node) in all_buget
        ]) <= budget)

    def _add_boolean_variabile(self,component,flavour,node):
        self.D[(component, flavour, node)] = Bool(
            f"{component}_{flavour}_{node}"
        )

    def _add_objective(self, component, flav, node,val):
        self.objective_f.append(
            val * self.D[(component, flav, node)]
        )

        # for i,c in enumerate(self.constraints):
        #    opt.assert_and_track(c, str(c))

        # for component in self.intermediate.comps:
        #     for flav in self.intermediate.flav[component]:
        #         for node in self.intermediate.nodes:
        #             if f"{component}_{flav}_{node}" in ['hour_large_node3', 'life_large_node4', 'ok_large_node1', 'also_large_node1', 'watch_large_node5']:
        #                 opt.add(self.D[(component, flav, node)] == True)
        #             else:
        #                 opt.add(self.D[(component, flav, node)] == False)
