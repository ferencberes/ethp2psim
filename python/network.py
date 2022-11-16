import networkx as nx
import numpy as np

class Network:
    """Peer-to-peer network abstraction"""
    
    def __init__(self, num_nodes: int=100, k: int=5, graph: nx.Graph=None, seed: int=None, node_weght: str="random"):
        """
        Parameters
        ----------
        num_nodes : int
            Number of nodes in the peer-to-peer graph
        k : int
            Regularity parameter
        graph : networkx.Graph
            Provide custom graph otherwise a k-regular random graph is generated
        seed: int (optional)
            Random seed (disabled by default)
        """
        self._rng = np.random.default_rng(seed)
        self._generate_graph(num_nodes, k, graph)
        
    def _generate_graph(self, num_nodes: int, k: int, graph: nx.Graph=None):
        if graph is not None:
            self.graph = graph
            self.k = -1
        else:
            self.graph = nx.random_regular_graph(k, num_nodes)
            self.k = k
        # NOTE: random edge weights (p2p latencies)
        # self.edge_weights = dict(zip(self.graph.edges, np.random.random(self.graph.number_of_edges())))
        # NOTE: custom edge weights (p2p latencies)
        # See Table 2 here: https://arxiv.org/pdf/1801.03998.pdf
        self.edge_weights = dict(zip(self.graph.edges, np.random.normal(loc=171, scale=76, size=self.graph.number_of_edges())))
        # NOTE: implement custom node weights
        if node_weight == "random":
            self.node_weights = dict(zip(self.graph.nodes, np.random.random(self.num_nodes)))
        # NOTE: nodes are weighted by their staked ether ratio.
        # This is the probability they will be chosen to propose the next block.
        elif node_weight == "stake":
            pdf = np.load(open('figures/sendingProbabilities.npy', 'rb'), allow_pickle=True)
            pdf = pdf/np.sum(pdf)
            self.node_weights = dict(zip(self.graph.nodes, pdf[:num_nodes]))
        
    @property
    def num_nodes(self):
        return self.graph.number_of_nodes()
        
    def sample_random_nodes(self, count: int, replace: bool, use_weights: bool=False, exclude: list=None):
        """
        Sample network nodes uniformly at random
        
        Parameters
        ----------
        count : int
            Number of nodes to sample
        replace : bool
            Whether the sample is with or without replacement
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
        if use_weights:
            return self._rng.choice(nodes, count, replace=replace, p=probas_arr)
        else:
            return self._rng.choice(nodes, count, replace=replace)