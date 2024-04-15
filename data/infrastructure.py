from data.node import Node
from data.link import Link
from pydantic import BaseModel

class Infrastructure(BaseModel):
    nodes: dict[str, Node] = {}
    links: list[Link] = []

    def add_node(self, name):
        self.nodes[name] = Node(name)

    def add_link(self, node1, node2):
        self.links.append(Link(node1, node2))