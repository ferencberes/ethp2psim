import pandas as pd
import numpy as np
from protocols import ProtocolEvent
from network import Network

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
        """Abstraction for the entity that tries to deanonymize Ethereum addresses by observing p2p network traffic"""
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
        """Adversary records the observed information"""
        self.captured_events.append(ee)
        self.captured_msgs.add(ee.mid)
        
    def predict_msg_source(self):
        """Predict source nodes for each message"""
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