import operator

# Requirement definition - Requirements are triples <name,value,soft>
class Requirement:
    def __init__(self, name, value, soft=False):
        self._name = name
        self._value = Property(value)

        if not isinstance(soft, bool):
            raise ValueError("The requirement property 'soft' must be boolean")
        self._soft = soft

    @property
    def name(self):
        return self._name
    
    @property
    def value(self):
        return self._value
    
    @property
    def soft(self):
        return self._soft


# Component requirement definition
class ComponentRequirement(Requirement):
    def __init__(self, name, value, soft=False):
        super().__init__(name, value, soft)
        self._general = True
        #self._flavour_specific = {}
    
    @property
    def general(self):
        return self._general
    
    def setGeneral(self, general=True):
        self._general = general


class FlavourRequirement(Requirement):
    def __init__(self, flavour, name, value, soft=False):
        super().__init__(name, value, soft)
        self._general = False
        self._flavour_specific = {}
    
    @property
    def flavours(self):
        return self._flavour_specific
    
    def setFlavourSpecific(self, flavour, req_name):
        self._flavour_specific[flavour] = req_name


# Properties definitions, this will allow us to set the values as desire
class Property:
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

class NumericProperty(Property):
    def __init__(self, value):
        if not isinstance(value, (int, float)):
            raise ValueError("A numeric Property value must be int or float")
        super().__init__(value)

class StringProperty(Property):
    def __init__(self, value):
        if not isinstance(value, str):
            raise ValueError("A string Property value must be a string")
        super().__init__(value)

class SecurityProperty(Property):
    def __init__(self, value):
        super().__init__(value)


