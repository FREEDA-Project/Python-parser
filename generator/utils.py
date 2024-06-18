from faker import Faker
import random
POSSIBLE_FLAVOURS = ['tiny', 'medium', 'large']
POSSIBILE_REQ_COMP = ['availability', 'ram', 'cpu', 'storage', 'bwIn', 'bwOut', 'security']
POSSIBILE_SECURITY_REQ = ['ssl', 'firewall', 'encrypted_storage']
POSSIBILE_REQ_DEPENDENCY = ['latency', 'availability']

fake = Faker()

def generate_dep(name,old_val=None, is_node=False):
    if name =='ram':
        min_val = 1 if old_val is None else old_val
        max_val = 10 if not is_node else 30
        return fake.random_int(min=min_val, max=max_val)
    elif name == 'cpu':
        min_val = 1 if old_val is None else old_val
        max_val = 4 if not is_node else 12
        return fake.random_int(min=min_val, max=max_val)
    elif name == 'storage':
        min_val = 800 if old_val is None else old_val
        max_val = 1000 if not is_node else 4500
        return fake.random_int(min=min_val, max=max_val)
    elif name == 'bwIn':
        min_val = 50 if old_val is None else old_val
        max_val = 100 if not is_node else 450
        return fake.random_int(min=min_val, max=max_val)
    elif name == 'bwOut':
        min_val = 50 if old_val is None else old_val
        max_val = 100 if not is_node else 450
        return fake.random_int(min=min_val, max=max_val)
    elif name == 'security':
        k= 1 if random.random() < 0.1 else 0
        if is_node:
            k = int(random.gammavariate(2, 2))
            k = min(k,len(POSSIBILE_SECURITY_REQ))
        randoms = random.sample(POSSIBILE_SECURITY_REQ, k=k)
        if old_val is not None:
            randoms = randoms + old_val
            randoms = list(set(randoms))
        return randoms
    elif name == 'availability':
        min_val = 80 if old_val is None else old_val
        max_val = 90 if not is_node else 100
        return fake.random_int(min=min_val, max=max_val)
    elif name == 'latency':
        min_val = 90 #if old_val is None else old_val
        max_val = 100 if not is_node else 94
        return fake.random_int(min=min_val, max=max_val)
    else:
        print('Error: ',name)
