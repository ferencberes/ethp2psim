import networkx as nx
import uuid
import numpy as np
import pandas as pd

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

class ProtocolEvent:
    def __init__(self, node: int, delay: float, hops: int):
        """Message information propagated through the peer-to-peer network"""
        self.node = node
        self.delay = delay
        self.hops = hops
        
    def __repr__(self):
        return "ProtocolEvent(%i, %f, %i)" % (self.node, self.delay, self.hops)
        
class Protocol:
    def __init__(self, network: Network):
        """Abstraction for different message passing protocols"""
        self.network = network
        
    def propagate(self, pe: ProtocolEvent):
        return []
        
class BroadcastProtocol(Protocol):
    def __init__(self, network: Network):
        """Transaction propagation is based on broadcasting"""
        super(BroadcastProtocol, self).__init__(network)
    
    def propagate(self, pe: ProtocolEvent):
        new_events = []
        node = pe.node
        for neigh in self.network.graph.neighbors(node):
            link = (node, neigh)
            if not link in self.network.weights:
                link = (neigh, node)
            elapsed_time = pe.delay + self.network.weights[link]
            rec = ProtocolEvent(neigh, elapsed_time, pe.hops+1)
            new_events.append(rec)
        return new_events

class EavesdropEvent:
    def __init__(self, mid: str, source: int, sender:int, pe:ProtocolEvent):
        """Information related to the observed message"""
        self.mid = mid
        self.source = source
        self.sender = sender
        self.protocol_event = pe
        
    def __repr__(self):
        return "EavesdropEvent(%s, %i, %i, %s)" % (self.mid, self.source, self.sender, self.protocol_event)

class Adversary: 
    def __init__(self, network: Network, ratio: float, seed: int=None):
        self.nodes = []
        self.candidates = list(network.graph.nodes())
        self.captured_events = []
        self.captured_msgs = set()
        """Each node is adversarial according to the ratio probability"""
        if seed != None:
            np.random.seed(seed)
        for idx, score in enumerate(np.random.random(size=len(self.candidates))):
            if score < ratio: 
                self.nodes.append(self.candidates[idx])
                
    def eavesdrop_msg(self, ee:EavesdropEvent):
        self.captured_events.append(ee)
        self.captured_msgs.add(ee.mid)
        
    def predict_msg_source(self):
        first_seen = {}
        predicted_node = {}
        for ee in self.captured_events:
            message_id = ee.mid
            sender = ee.sender
            delay = ee.protocol_event.delay
            if (not message_id in first_seen) or delay < first_seen[message_id]:
                first_seen[message_id] = delay
                predicted_node[message_id] = sender
        predictions = pd.DataFrame(np.zeros((len(self.captured_msgs), len(self.candidates))), columns=self.candidates, index=list(self.captured_msgs))        
        for mid, node in predicted_node.items():
            predictions.at[mid, node] = 1.0
        return predictions
        
class Message:
    def __init__(self, source: int):
        """Abstraction for Ethereum transactions"""
        self.mid = uuid.uuid4().hex
        self.source = source
        # TODO: check existence!
        self.history = {source:ProtocolEvent(self.source, 0.0, 0)}
        self.queue = [source]
        
    def process(self, protocol: Protocol, adv: Adversary):
        """Propagate the message on outbound links"""
        new_queue = []
        for sender in self.queue:
            new_events = protocol.propagate(self.history[sender])
            for rec in new_events:
                receiver = rec.node
                if not receiver in self.history:
                    self.history[receiver] = rec
                    new_queue.append(receiver)
                    # adversary only records first message contact
                    if receiver in adv.nodes:
                        adv.eavesdrop_msg(EavesdropEvent(self.mid, self.source, sender, rec))
        self.queue = new_queue
        return len(self.history) / protocol.network.num_nodes