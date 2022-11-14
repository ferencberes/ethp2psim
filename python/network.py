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
        
    def _generate_graph(self, num_nodes: int, k: int, graph: nx.Graph=None):
        if graph is not None:
            self.graph = graph
            self.k = -1
        else:
            self.graph = nx.random_regular_graph(k, num_nodes)
            self.k = k
        # NOTE: implement custom edge weights
        self.edge_weights = dict(zip(self.graph.edges, np.random.random(self.graph.number_of_edges())))
        # NOTE: implement custom node weights
        self.node_weights = dict(zip(self.graph.nodes, np.random.random(self.num_nodes)))
        
    @property
    def num_nodes(self):
        return self.graph.number_of_nodes()
    
    def sample_random_nodes(self, count: int, use_weights: bool=False, exclude: list=None, seed=None):
        """
        Sample network nodes uniformly at random
        
        Parameters
        ----------
        count : int
            Number of nodes to sample
        use_weights : bool
            Set to sample nodes with respect to their weights
        exclude : list
            List of nodes to exclude from the sample
        """
        nodes = list(self.graph.nodes())
        weights = self.node_weights.copy()
        if exclude is not None:
            intersection = np.intersect1d(nodes, exclude)
            for node in intersection:
                nodes.remove(node)
                del weights[node]
        sum_weights = np.sum(list(weights.values()))
        probas_arr = [weights[node] / sum_weights  for node in nodes]
        if seed != None:
            np.random.seed(seed)
        if use_weights:
            return np.random.choice(nodes, count, replace=True, p=probas_arr)
        else:
            return np.random.choice(nodes, count, replace=True)