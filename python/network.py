import networkx as nx
import numpy as np

class Network:
    def __init__(self, num_nodes: int=100, k: int=5, graph: nx.Graph=None):
        """Peer-to-peer network abstraction"""
        self.generate_graph(num_nodes, k, graph)
        
    def generate_graph(self, num_nodes, k, graph: nx.Graph=None):
        if graph is not None:
            self.graph = graph
            self.k = -1
        else:
            self.graph = nx.random_regular_graph(k, num_nodes)
            self.k = k
        # NOTE: implement custom edge weights
        self.weights = dict(zip(self.graph.edges, np.random.random(self.graph.number_of_edges())))
        
    @property
    def num_nodes(self):
        return self.graph.number_of_nodes()