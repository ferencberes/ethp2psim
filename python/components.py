import networkx as nx
import uuid
import numpy as np

class Network:
    def __init__(self, num_nodes: int=100, k: int=5):
        """Peer-to-peer network abstraction"""
        self.num_nodes = num_nodes
        self.k = k
        self.generate_graph()
        
    def generate_graph(self):
        success = False
        self.graph = nx.random_regular_graph(self.k, self.num_nodes)
        # NOTE: implement custom edge weights
        self.weights = dict(zip(self.graph.edges, np.random.random(self.graph.number_of_edges())))
        
class Message:
    def __init__(self, sender: int):
        self.mid = uuid.uuid4().hex
        self.sender = sender
        # NOTE: implement custom latency calculation
        self.start = 0.0
        self.history = dict()
        # initial state
        self.queue = [(self.sender, self.start)]
        
    def process(self, network: Network):
        new_queue = []
        for node, elapsed_time in self.queue:
            # NOTE: implement custom neighbor calculation
            for neigh in network.graph.neighbors(node):
                if not neigh in self.history:
                    link = (node, neigh)
                    if not link in network.weights:
                        link = (neigh, node)
                    current_time = elapsed_time + network.weights[link]
                    self.history[neigh] = current_time
                    new_queue.append((neigh, current_time))
        self.queue = new_queue
        return len(self.history) / network.num_nodes