import networkx as nx
import uuid
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

class Record:
    def __init__(self, node: int, delay: float, hops: int):
        """Message information propagated through the peer-to-peer network"""
        self.node = node
        self.delay = delay
        self.hops = hops
        
class Protocol:
    def __init__(self, network: Network):
        """Abstraction for different message passing protocols"""
        self.network = network
        
class BroadcastProtocol(Protocol):
    def __init__(self, network: Network):
        """Transaction propagation is based on broadcasting"""
        super(BroadcastProtocol, self).__init__(network)
    
    def propagate(self, record: Record):
        new_records = []
        node = record.node
        for neigh in self.network.graph.neighbors(node):
            link = (node, neigh)
            if not link in self.network.weights:
                link = (neigh, node)
            elapsed_time = record.delay + self.network.weights[link]
            rec = Record(neigh, elapsed_time, record.hops+1)
            new_records.append(rec)
        return new_records
    
class Adversary: 
    def __init__(self, network: Network, ratio: float, seed: int=None):
        self.nodes = []
        self.captured_msgs = []
        """Each node is adversarial according to the ratio probability"""
        if seed != None:
            np.random.seed(seed)
        for node_idx, score in enumerate(np.random.random(size=network.num_nodes)):
            if score < ratio: 
                self.nodes.append(node_idx)
                
    def eavesdrop_msg(msg: Record):
        self.captured_msgs.append(msg)
        
class Message:
    def __init__(self, sender: int):
        """Abstraction for Ethereum transactions"""
        self.mid = uuid.uuid4().hex
        self.sender = sender
        # TODO: check existence!
        self.history = {sender:Record(self.sender, 0.0, 0)}
        self.queue = [sender]
        
    def process(self, protocol: Protocol, adv: Adversary):
        """Propagate the message on outbound links"""
        new_queue = []
        for node in self.queue:
            new_records = protocol.propagate(self.history[node])
            for rec in new_records:
                if not rec.node in self.history:
                    self.history[rec.node] = rec
                    new_queue.append(rec.node)
        self.queue = new_queue
        return len(self.history) / protocol.network.num_nodes