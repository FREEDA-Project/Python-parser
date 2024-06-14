from translator.translator import Translator
from abc import abstractmethod
from config import DEBUG
from translator.intermediate_language import IntermediateLanguage


class SolverTranslator(Translator):
    def __init__(self, intermediate_language: IntermediateLanguage) -> None:
        self.intermediate = intermediate_language
        self.constraints=[]

    @abstractmethod
    def _add_at_most_on_flav_and_node(self,conponent):
       pass

    @abstractmethod
    def _add_must_component(self,conponent):
       pass

    @abstractmethod
    def _add_deploy_used_component(self,conponent,flav,use):
       pass

    @abstractmethod
    def _add_total(self,budget,all_buget):
        pass

    @abstractmethod
    def _add_impossibile_deploy(self,component,flav,node):
        pass

    @abstractmethod
    def _add_comulative_constaint(self,val,component_requirements):
        pass

    @abstractmethod
    def _add_impossibile_combination(self,component,flav,node,component1,flav1,node1):
        pass

    def _transform_requirements(self, name, value):
        if name == "latency":
            return -value
        return value

    def add_constraint(self, constraint):
        if DEBUG:
            print(constraint)
        if isinstance(constraint, list):
            self.constraints.extend(constraint)
        else:
            self.constraints.append(constraint)

    def generate_contraints(self):
        # 1.2
        if DEBUG:
            print(" --- deploy at most one flavour of a component on a node")
        for component in self.intermediate.comps:
            self._add_at_most_on_flav_and_node(component)
        # 1.3
        if DEBUG:
            print(" --- must component")
        for must in self.intermediate.mustComp:
            self._add_must_component(must)

        if DEBUG:
            print(" --- deploy used components ")
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    self._add_deploy_used_component(component,flav,use)

        # 1.3.1
        if DEBUG:
            print(" --- component requirements")
        not_compatible=set()
        # this could be done before creating the variabile actually, and skip the cration of this variabile
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for req, val in self.intermediate.comReq[component][flav].items():
                    for i, node in enumerate(self.intermediate.nodes):
                        val = self._transform_requirements(req, val)
                        if req in self.intermediate.nodeCap[node]:
                            node_cap = self._transform_requirements(
                                req, self.intermediate.nodeCap[node][req]
                            )
                            if not (val <= node_cap):
                                # can for multiple req so is better to set only one constraint
                                not_compatible.add((component,flav,node))
        for component,flav,node in not_compatible:
            self._add_impossibile_deploy(component,flav,node)

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
                        comp_val = self.intermediate.comReq[component][flav][req]
                        component_requirements.append(
                            (self._transform_requirements(req, comp_val)
                            ,(component, flav, node))
                        )
                val = self._transform_requirements(req, val)
                self._add_comulative_constaint(val,component_requirements)

        # 1.3.2
        if DEBUG:
            print(" --- link requirements")
        impossible_combinations = set()
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for use in self.intermediate.uses[component][flav]:
                    for uses_flav in self.intermediate.flav[use]:
                        for req, val in self.intermediate.get_dep_req(component, use):
                            val = self._transform_requirements(req, val)
                            for  node1 in (self.intermediate.nodes):
                                for  node2 in (self.intermediate.nodes):
                                    link_cap = self.intermediate.get_link_cap(node1, node2)
                                    if link_cap is None or req not in link_cap:
                                        continue
                                    linkCapVal = self._transform_requirements(
                                        req, link_cap[req]
                                    )

                                    if not (val <= linkCapVal):
                                        impossible_combinations.add((component,flav,node1,use,uses_flav,node2))

                                inter_node = self.intermediate.INTER_NODE()
                                if inter_node in self.intermediate.nodeCap[node1]:
                                    link_cap = self.intermediate.nodeCap[node1][inter_node]
                                    if link_cap is not None and not (val <= link_cap):
                                        impossible_combinations.add((component,flav,node1,use,uses_flav,node1))


        for component,flav,node1,use,uses_flav,node2 in impossible_combinations:
            self._add_impossibile_combination(component,flav,node1,use,uses_flav,node2)
        # 1.3.3
        if DEBUG:
            print(" --- budget requirements")
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
                        comp_val = self.intermediate.comReq[component][flav][req_comp]
                        if "carbon" == req:
                            total_cons.append(
                                (comp_val , val , (component, flav, node))
                            )
                        else:
                            total_cost.append(
                                (comp_val , val , (component, flav, node))
                            )

        self._add_total(self.intermediate.budget_carbon,total_cons)
        self._add_total(self.intermediate.budget_cost,total_cost)

    @abstractmethod
    def _add_boolean_variabile(self,component,flavour,node):
        pass

    def add_variables(self):
        for component in self.intermediate.comps:
            for flavour in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    self._add_boolean_variabile(component,flavour,node)


    @abstractmethod
    def _add_objective(self, component, flav, node,val):
        pass

    def objective(self):
        for component in self.intermediate.comps:
            for flav in self.intermediate.flav[component]:
                for node in self.intermediate.nodes:
                    val = IntermediateLanguage.flav_to_importance(flav)
                    self._add_objective(
                        component, flav, node,val
                    )
