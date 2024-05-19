## this file generates a random application
import random
from utils import fake, generate_dep,POSSIBILE_REQ_COMP,POSSIBLE_FLAVOURS,POSSIBILE_REQ_DEPENDENCY,POSSIBILE_SECURITY_REQ

def generate_with_n_components(component_number:int):
    components_name= list(
        "component"+ str(i) for i in range(component_number)
    )
    
    components = {
        name:generate_component(name, components_name) for name in components_name
    }

    requirements = {
        "components": {
            name: generate_reqirements(components[name]) for name in components_name
        },
    }
    requirements["dependencies"]=  generate_dependency(components)
    requirements["budget"] ={
            "cost": fake.random_number(digits=5),
            "carbon": fake.random_number(digits=3)
        }

    return {
        "name": fake.company(),
        "components": components,
        "requirements": requirements,
    }



# Function to generate component data
def generate_component(name,otherComponents):
    otherComponents = list(filter(lambda x: x != name, otherComponents))
    comp = {
        "type": "service",
        "must": fake.boolean(),
    }
    flavs= random.sample(POSSIBLE_FLAVOURS, k=random.randint(1, len(POSSIBLE_FLAVOURS)))
    if len(flavs) > 0:  
        comp["flavours"] = { }
        used = []
        for flav in POSSIBLE_FLAVOURS:
            if flav in flavs:
                if random.random() < 0.5:
                    gamma_value = int(random.gammavariate(1, 2))
                    if gamma_value >= len(otherComponents):
                        gamma_value = len(otherComponents)    
                    used.extend(random.sample(otherComponents, k=gamma_value))
                comp["flavours"][flav] = {}
                comp["flavours"][flav]['uses'] = list(set(used))
    return comp

def generate_dependency(components):
    done = set()
    def make_for_set(name1,name2):
        if name1 > name2:
            return (name2,name1)
        return (name1,name2)
    
    def check_flav(name1,name2):
        if name1 == name2:
            return False
        
        def get_used_comp_in_flav(name):
            if 'flavours' not in components[name]:
                return []
            c = [] 
            for comp in components[name]['flavours'].values():
                c.extend(comp['uses'])
            return list(set(c))

        used1 = get_used_comp_in_flav(name1)
        used2 = get_used_comp_in_flav(name2)

        if name1 in used2 or name2 in used1:
            return True
        return False        

    dep = {}
    for name1 in components:
        for name2 in components:
            if check_flav(name1,name2) and make_for_set(name1,name2) not in done: 
                if make_for_set(name1,name2) not in done:
                    dep[name1] = dep.get(name1,{})
                    dep[name1][name2] = dep.get(name2,{})
                    for req in POSSIBILE_REQ_DEPENDENCY:
                        dep[name1][name2][req] = {
                                'value': generate_dep(req),
                                'soft': fake.boolean()
                        }
                    done.add(make_for_set(name1,name2))
    return dep



def generate_reqirements(component):
    # randomize which 
    flavours = component['flavours']
    # from POSSIBILE_REQ_COMP split in two random list
    common_req = POSSIBILE_REQ_COMP.copy()
    flav_req = []
    if len(flavours)!=0:
        random.shuffle(common_req)
        i = random.randint(1,len(common_req))
        comp_req = POSSIBILE_REQ_COMP[:i]
        flav_req = POSSIBILE_REQ_COMP[i:]

    common = { }       

    for req in comp_req:
        common[req] = {
            "value": generate_dep(req),
            "soft": fake.boolean()
        }
    flav_dict = {}

    for flav in POSSIBLE_FLAVOURS:
        old = {}
        if flav in flavours:
            flav_reqs = {}
            for req in flav_req:
                flav_reqs[req]={
                    "value": generate_dep(req,old.get(req)),
                    "soft": fake.boolean()
                }
                old[req] = flav_reqs[req]['value']
            flav_dict[flav] = flav_reqs
    return {
        "common": common,
        "flavour-specific": flav_dict
    }
        

