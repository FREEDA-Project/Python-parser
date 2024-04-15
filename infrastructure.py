from requirement import Property
from application import Budget

class Infrastructure:
    def __init__(self):
        self._nodes = {}
        self._links = []

    @property
    def nodes(self):
        return self._nodes
    
    @property
    def links(self):
        return self._links
    
    def add_node(self, name):
        self._nodes[name] = Node(name)

    def add_link(self, node1, node2):
        self._links.append(Link(node1, node2))


# Node definition 
class Node:
    def __init__(self, name):
        if not isinstance(name, str):
            raise ValueError("The name of a node must be a string")
        self._name = name
        self._capabilities = {}
        self._profile = {}

    @property
    def name(self):
        return self._name

    @property
    def capabilities(self):
        return self._capabilities

    @property
    def profile(self):
        return self._profile
    
    def add_capability(self, name, value):
        self._capabilities[name] = Capability(name, value)
    
    def set_profile(self, cost, carbon):
        self._profile = Budget(cost, carbon)
    

# Link definition
class Link:
    def __init__(self, node1, node2):
        self._pair = (node1, node2)
        self._capabilities = {}
    
    @property
    def pair(self):
        return self._pair
    
    @property
    def capabilities(self):
        return self._capabilities
    
    def add_capability(self, name, value):
        self._capabilities[name] = Capability(name, value)


# Capability definition
class Capability:
    def __init__(self, name, value):
        if not isinstance(name, str):
            raise ValueError("The name of a capability must be a string")
        self._name = name
        self._value = Property(value)

    @property
    def name(self):
        return self._name
    
    @property
    def value(self):
        return self._value
