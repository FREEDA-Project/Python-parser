from requirement import ComponentRequirement

class Component:
    # type (should be 'service', 'database', or 'integration')
    valid_types = ["service", "database", "integration"]

    def __init__(self, name, type, must=False):
        if not isinstance(name, str):
            raise ValueError("The name of a component must be a string")
        self._name = name

        if not type:
            raise ValueError("The type of a component cannot be empty")
        if not isinstance(type, str):
            raise ValueError("The type of a component must be a string")
        if type.lower() not in self.valid_types:
            raise ValueError(f"Invalid component type: {type}, it should be one of the followings: {self.valid_types}")
        self._type = type

        if not isinstance(must, bool):
            raise ValueError("The 'must' attribute of a compoenent must be boolean")
        self._must = must

        self._flavours = {}
        self._requirements= {}

    @property
    def name(self):
        return self._name
    
    @property
    def type(self):
        return self._type
    
    @property
    def must(self):
        return self._must
    
    @property
    def flavours(self):
        return self._flavours
    
    @property
    def component_requirements(self):
        return self._requirements

    def add_flavour(self, flavour, uses):
        self.flavours[flavour] = uses
    
    def add_component_requirement(self, name, value, soft=False):
        try:
            self._requirements[name] = ComponentRequirement(name, value, soft)
        except ValueError as e:
            print(f"Error: {e}")

    def add_flavour_requirement(self, flavour, req_name, req_value, req_soft=False):
        try:
            self._requirements[req_name] = FlavourRequirement(flavour, req_name, req_value, req_soft)
        except ValueError as e:
            print(f"Error: {e}")