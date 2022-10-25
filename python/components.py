import networkx as nx
import uuid
import numpy as np

class Network:
    def __init__(self, num_nodes: int=100, k: int=5, graph: nx.Graph=None):
        """Peer-to-peer network abstraction"""
        self.num_nodes = num_nodes
        self.k = k
        self.generate_graph(graph)
        
    def generate_graph(self, graph: nx.Graph=None):
        success = False
        if graph is not None:
            self.graph = graph
            self.num_nodes = self.graph.number_of_nodes()
            self.k = -1
        else:
            self.graph = nx.random_regular_graph(self.k, self.num_nodes)
        # NOTE: implement custom edge weights
        self.weights = dict(zip(self.graph.edges, np.random.random(self.graph.number_of_edges())))

class Record:
    def __init__(self, node: int, delay: float, hops: int):
        """Message information propagated through the peer-to-peer network"""
        self.node = node
        self.delay = delay
        self.hops = hops
        
class Message:
    def __init__(self, sender: int):
        """Abstraction for Ethereum transactions"""
        self.mid = uuid.uuid4().hex
        self.sender = sender
        self.history = {sender:Record(self.sender, 0.0, 0)}
        self.queue = [sender]
        
    def process(self, network: Network):
        """Propagate the message on outbound links"""
        new_queue = []
        for node in self.queue:
            record = self.history[node]
            # NOTE: implement custom neighbor calculation
            for neigh in network.graph.neighbors(node):
                if not neigh in self.history:
                    link = (node, neigh)
                    if not link in network.weights:
                        link = (neigh, node)
                    elapsed_time = record.delay + network.weights[link]
                    new_record = Record(neigh, elapsed_time, record.hops+1)
                    self.history[neigh] = new_record
                    new_queue.append(neigh)
        self.queue = new_queue
        return len(self.history) / network.num_nodes