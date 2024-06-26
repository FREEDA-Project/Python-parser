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
