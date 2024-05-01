
class _UnionFind:
    def __init__(self, array:list[str]):
        self.node_to_index= {node:i for i, node in enumerate(array)}
        self.index_to_node= {i:node for i, node in enumerate(array)}
        n = len(array)
        self.parent = list(range(n))


    def find(self, x:str)->str:
        return self.index_to_node[self._find(self.node_to_index[x])]

    def union(self, x:str, y:str):
        self._union(self.node_to_index[x], self.node_to_index[y])

    def _find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self._find(self.parent[x])
        return self.parent[x]

    def _union(self, x, y):
        root_x = self._find(x)
        root_y = self._find(y)
        if root_x != root_y:
            self.parent[root_y] = root_x


    def get_roots(self)->list[str]:
        return [self.index_to_node[i] for i in self._get_roots()]

    def _get_roots(self)->list[int]:
        return [i for i, node in enumerate(self.index_to_node) if self.parent[i] == i]

def _inverse_graph(graph:dict[str,list[str]])->dict[str,list[str]]:
    inverse_graph = { node:[] for node in graph }
    for node, children in graph.items():
        for child in children:
            inverse_graph[child].append(node)
    return inverse_graph


def _trojan(graph:dict[str,list[str]]):
    visited = set()
    order = []
    component = []
    def dfs1(current:str):
        visited.add(current)
        for child in graph[current]:
            if child not in visited:
                dfs1(child)
        order.append(current)

    inverse_graph = _inverse_graph(graph)
    def dfs2(current:str):
        visited.add(current)
        component.append(current)
        for child in inverse_graph[current]:
            if child not in visited:
                dfs2(child)
    
    for node in graph:
        if node not in visited:
            dfs1(node)

    visited = set() 

    union_find= _UnionFind(list(graph.keys()))
        
    for node in order[::-1]:
        if node not in visited:
            component = []
            dfs2(node)
            for c_node in component:
                union_find.union(node, c_node)
    
    # create a new graph where the node in the same component are a single node
    new_graph = {node:[] for node in union_find.get_roots()}

    # update the new graph
    for node, children in graph.items():
        node = union_find.find(node)
        for child in children:
            child= union_find.find(child)
            if child!=node:
                new_graph[node].append(child)
    inverse_graph = _inverse_graph(new_graph)
    roots = list(filter(lambda x: len(inverse_graph[x]) == 0, new_graph.keys()))
    
    uf_roots = set(roots)
    res = []
    for node in graph.keys():
        if union_find.find(node) in uf_roots:
            res.append(node)

    return res


def get_roots(graph:dict[str,list[str]])->list[str]:
    """
    Get the root nodes of a graph.
    
    Args:
        graph (dict[str, list[str]]): A graph represented as a dictionary where the keys are the nodes and the values are the nodes that the key node points to.
    
    Returns:
        list[str]: A list of the root nodes of the graph.
    """
    return _trojan(graph)




