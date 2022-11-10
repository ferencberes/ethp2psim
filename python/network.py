import networkx as nx
import numpy as np

class Network:
    """Peer-to-peer network abstraction"""
    
    def __init__(self, num_nodes: int=100, k: int=5, graph: nx.Graph=None):
        """
        Parameters
        ----------
        num_nodes : int
            Number of nodes in the peer-to-peer graph
        k : int
            Regularity parameter
        graph : networkx.Graph
            Provide custom graph otherwise a k-regular random graph is generated
        """
        self._generate_graph(num_nodes, k, graph)
        
    def _generate_graph(self, num_nodes, k, graph: nx.Graph=None):
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
    
    def sample_random_sources(self, count):
        """
        Sample network nodes uniformly at random
        
        Parameters
        ----------
        count : int
            Number of nodes to sample
        """
        return np.random.randint(0, self.num_nodes-1, count)