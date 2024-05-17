from z3 import (
    Bool,
    Optimize,
    Sum,
    sat,
)
from config import DEBUG
from translator.intermediate_language import IntermediateLanguage
from translator.solver_translator import SolverTranslator


class Z3Translator(SolverTranslator):

    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate = intermediate_language

    def to_file_string(self) -> str:
        return self.gen_problem().model()
    
    def gen_problem(self):
        self.D={}
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
            # get the variable that are true
            return [str(k) for k in model if model[k]]
        else:
            return None
        

    def _transform_requirements(self, name, value):
        if name == "latency":
            return -value
        return value


    def _add_at_most_on_flav_and_node(self, component):
        self.add_constraint(
            Sum(
                [
                    self.D[(component, f, n)]
                    for f in self.intermediate.flav[component]
                    for n in self.intermediate.nodes
                ]
            )
            <= 1
        )
    def _add_must_component(self, must):
        self.add_constraint(
                Sum(
                    [
                        self.D[(must, f, n)]
                        for f in self.intermediate.flav[must]
                        for n in self.intermediate.nodes
                    ]
                )
                == 1,
        )

    def _add_deploy_used_component(self, component, flav, use):
        self.add_constraint(
            Sum(
                [
                    self.D[(component, flav, node)]
                    for node in self.intermediate.nodes
                ]
            )
            <= Sum(
                [
                    self.D[(use, flavUse, node)]
                    for flavUse in self.intermediate.flav[use]
                    for node in self.intermediate.nodes
                ]
            )
        )

    def _add_impossibile_deploy(self, component, flav, node):
        self.add_constraint(self.D[(component,flav,node)]==False)

    def _add_comulative_constaint(self, val, component_requirements):
        self.add_constraint(
            Sum(
            [    self.D[(c, f, n)] * v for v, (c, f, n) in component_requirements]
            )
            <= val
        )
    def _add_impossibile_combination(
        self, component, flav, node, component1, flav1, node1
    ):
        self.add_constraint(
                Sum(self.D[(component,flav,node)], self.D[(component1,flav1,node1)])<=1
        )

    def _add_total(self, budget, all_buget):
        self.add_constraint(
            Sum([
                val * comp_val * self.D[(component, flav, node)]
                for comp_val, val, (component, flav, node) in all_buget
            ]
            )
            <= budget
        )

    def _add_boolean_variabile(self,component,flavour,node):
        self.D[(component, flavour, node)] = Bool(
            f"{component}_{flavour}_{node}"
        )

    def _add_objective(self, component, flav, node,val):
        self.objective_f.append(
            val * self.D[(component, flav, node)]
        )

# TO debug
# for i,c in enumerate(self.constraints):
#    opt.assert_and_track(c, str(i))

# for component in self.intermediate.comps:
#    for flav in self.intermediate.flav[component]:
#        for node in self.intermediate.nodes:
#            if (flav=='medium' and component=='frontend' and node =='n3')\
#            or (flav=='tiny' and component=='backend' and node=='n3'):
#                opt.add(D[(component, flav, node)] == True)
#            else:
#                opt.add(D[(component, flav, node)] == False)
