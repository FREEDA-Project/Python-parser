import yaml
from component import Component
from requirement import Requirement

class Application:
    def __init__(self, name):
        if not isinstance(name, str):
            raise ValueError("The name of the application must be a string")
        self._name = name
        self._components = {}
        self._dependencies = {}
        self._budget = {}

    @property
    def name(self):
        return self._name
    @property
    def components(self):
        return self._components
    @property
    def dependencies(self):
        return self._dependencies
    @property
    def budget(self):
        return self._budget

    def add_component(self, name, component_type, must=False):
        try:
            self._components[name] = Component(name, component_type, must)
        except ValueError as e:
            print(f"Error: {e}")

    def add_dependency(self, source, flavour, target):
        try:
            self._dependencies[source] = Dependency(source, flavour, target)
        except ValueError as e:
            print(f"Error: {e}")

    def add_budget(self, cost, carbon):
        self._budget = Budget(cost, carbon)



# Dependency definition
class Dependency:
    def __init__(self, source, flavour, target):
        if not isinstance(source, str):
            raise ValueError("The 'source' service on a dependency must be a string")
        self._source = source

        if not isinstance(flavour, str):
            raise ValueError("The 'flavour' on a dependency must be a string")
        self._flavour = flavour

        if not isinstance(target, str):
            raise ValueError("The 'target' service on a dependency must be a string")
        self._target = target

        self._requirements = {}

    @property
    def source(self):
        return self._source
        
    @property
    def flavour(self):
        return self._flavour
        
    @property
    def target(self):
        return self._target
    
    @property
    def requirements(self):
        return self._requirements
    
    def add_requirement(self, name, value, soft=False):
        self._requirements[name] = Requirement(name, value, soft)
        

# Budget definition - Budget is a pair b = <cost,gCO2-eq/KWh> which expresses how much the application administrator is willing to pay for the deployment of his application
class Budget:
    def __init__(self, cost, carbon):
        if not isinstance(cost, (int, float)):
            raise ValueError("Cost must be a numeric value")
        self._cost = cost

        if not isinstance(carbon, (int, float)):
            raise ValueError("Carbon must be a numeric value")
        self._carbon = carbon

    @property
    def cost(self):
        return self._cost

    @property
    def carbon(self):
        return self._carbon


# Read data
with open('parser/example.yaml', 'r') as yaml_file:
    data = yaml.safe_load(yaml_file)

# Create an application instance
app = Application(data['name'])

# setting components with flavours and requirements
for component_name, component_data in data['components'].items():
    component_type = component_data['type']
    must = component_data.get('must', False)
    app.add_component(component_name, component_type, must)
    #adding flavours
    for flavour, uses in component_data.get('flavours', {}).items():
        app.components[component_name].add_flavour(flavour, uses)

#adding requirements to each component
for component_name, reqs_component_data in data['requirements']['components'].items():
    #adding general requirements
    for req_name, req_data in reqs_component_data['common'].items():
        req_value = req_data.get('value')
        req_soft = req_data.get('soft', False)
        app.components[component_name].add_component_requirement(req_name, req_value, req_soft)
        app.components[component_name].component_requirements[req_name].setGeneral(True)
    #adding flavour specific requirements
    for flavour_name, flavour_data in reqs_component_data['flavour-specific'].items():
        for req_name, req_data in flavour_data.items():
            req_value = req_data.get('value')
            req_soft = req_data.get('soft', False)
            app.components[component_name].add_component_requirement(req_name, req_value, req_soft)
            app.components[component_name].component_requirements[req_name].setGeneral(False)
            app.components[component_name].component_requirements[req_name].setFlavourSpecific(flavour_name, req_name)

# Print information to check 
print(app.name)
for component_name, component in app.components.items():
    print(f"{component_name}: Type: {component.type}, Must: {component.must}")
    for flavour, uses in component.flavours.items():
        print(f"{flavour}: {uses}")
    print("Component requirements: (common)")
    for req_name, req_data in component.component_requirements.items():
        if(req_data.general):
            print(f"{req_name}: {req_data.value.value}, soft: {req_data.soft}, general requirement: {req_data.general}")
    print("Component requirements: (Flavour-specific)")
    for req_name, req_data in component.component_requirements.items():
        if not (req_data.general):
            print(f"{req_name}: {req_data.value.value}, soft: {req_data.soft}, general requirement: {req_data.general}")
    print()