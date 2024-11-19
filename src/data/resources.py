default_resources = {
    'cpu': {'type': 'consumable', 'optimization': 'minimization', 'worst_bound': 0},
    'ram': {'type': 'consumable', 'optimization': 'minimization', 'worst_bound': 0},
    'storage': {'type': 'consumable', 'optimization': 'minimization', 'worst_bound': 0},
    'bwIn': {'type': 'consumable', 'optimization': 'minimization', 'worst_bound': 0},
    'bwOut': {'type': 'consumable', 'optimization': 'minimization', 'worst_bound': 0},
    'security': {
        'choices': ['ssl', 'firewall', 'encrypted_storage'],
        'optimization': 'minimization', 'worst_bound': 0},
    'latency': {'type': 'non-consumable', 'optimization': 'maximization', 'best_bound': 0},
    'availability': {'type': 'non-consumable', 'optimization': 'minimization', 'best_bound': 100, 'worst_bound': 0}
}

class Resource:
    def __init__(
        self,
        name: str,
        consumable: bool,
        minimization: bool,
        best_bound: int = None,
        worst_bound: int = None
    ):
        self.name = name
        self.consumable = consumable
        self.minimization = minimization
        self.best_bound = best_bound
        self.worst_bound = worst_bound

    def __eq__(self, other):
        if isinstance(other, Resource):
            return self.name == other.name
        return False

class ListResource(Resource):
    def __init__(
        self,
        name: str,
        minimization: bool,
        choices: list[str],
    ):
        super().__init__(
            name,
            False,
            minimization,
            1,
            0
        )
        self.choices = choices
