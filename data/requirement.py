from data.property import Property
from pydantic import BaseModel

class Requirement(BaseModel):
    name: str
    value: Property
    soft:bool


# isn´t better to move general in requirement (if general is needed)
# and declare componentrequirement as
# ComponentRequirement = Requirement

class ComponentRequirement(Requirement):
    general:bool=True



class FlavourRequirement(Requirement):
    flavours_specific:dict[str, str]={}
    general:bool=False

    def setFlavourSpecific(self, flavour, req_name):
        self.flavours_specific[flavour] = req_name



