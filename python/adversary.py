import pandas as pd
import numpy as np
from protocols import ProtocolEvent
from network import Network

class EavesdropEvent:
    """Information related to the observed message"""
    
    def __init__(self, mid: str, source: int, sender:int, pe:ProtocolEvent):
        """
        Parameters
        ----------
        node : str
            Message identifier
        source : int
            Source node of the message
        sender : int
            Adversary received the message from this node
        protocol_event : protocols.ProtocolEvent
            Contains message spreading related information
        """
        self.mid = mid
        self.source = source
        self.sender = sender
        self.protocol_event = pe
        
    def __repr__(self):
        return "EavesdropEvent(%s, %i, %i, %s)" % (self.mid, self.source, self.sender, self.protocol_event)

class Adversary: 
    """Abstraction for the entity that tries to deanonymize Ethereum addresses by observing p2p network traffic"""
    
    def __init__(self, network: Network, ratio: float):
        """
        Parameters
        ----------
        network : network.Network
            Simulated P2P network
        ratio : float
            Fraction of adversary nodes in the P2P network
        """
        self.ratio = ratio
        self.candidates = list(network.graph.nodes())
        self.captured_events = []
        self.captured_msgs = set()
        self._sample_adversary_nodes(network)
            
    def _sample_adversary_nodes(self, network: Network):
        """Randomly select given fraction of nodes to be adversaries"""
        num_adversaries = int(len(self.candidates) * self.ratio)
        self.nodes = network.sample_random_nodes(num_adversaries, use_weights=False, replace=False)
                
    def eavesdrop_msg(self, ee:EavesdropEvent):
        """Adversary records the observed information"""
        self.captured_events.append(ee)
        self.captured_msgs.add(ee.mid)
        
    def _find_first_contact(self):
        contact_time = {}
        received_from = {}
        contact_node = {}
        for ee in self.captured_events:
            message_id = ee.mid
            sender = ee.sender
            delay = ee.protocol_event.delay
            if (not message_id in contact_time) or delay < contact_time[message_id]:
                contact_time[message_id] = delay
                received_from[message_id] = sender
                contact_node[message_id] = ee.protocol_event.node
        arr = np.zeros((len(self.captured_msgs), len(self.candidates)))
        empty_predictions = pd.DataFrame(arr, columns=self.candidates, index=list(self.captured_msgs))
        return contact_time, contact_node, received_from, empty_predictions
    
    def _first_reach_estimator(self):
        contact_time, contact_node, received_from, predictions = self._find_first_contact()
        for mid, node in received_from.items():
            predictions.at[mid, node] = 1.0
        return predictions
    
    def _dummy_estimator(self):
        N = len(self.candidates) - len(self.nodes)
        arr = np.ones((len(self.captured_msgs), len(self.candidates))) / N
        predictions = pd.DataFrame(arr, columns=self.candidates, index=list(self.captured_msgs))
        for node in self.nodes:
            predictions[node] *= 0
        return predictions
        
    def predict_msg_source(self, estimator: str="first_reach"):
        """
        Predict source nodes for each message
        
        By default, the node from whom the adversary first heard the message is assigned 1.0 probability while every other node receives zero.
        
        Parameters
        ----------
        estimator : {'first_reach', 'dummy'}, default 'first_reach'
            Strategy to assign probabilities to network nodes:
            * first_reach: the node from whom the adversary first heard the message is assigned 1.0 probability while every other node receives zero.
            * dummy: the probability is divided equally between non-adversary nodes.
        """
        if estimator == "first_reach":
            return self._first_reach_estimator()
        elif estimator == "dummy":
            return self._dummy_estimator()
        else:
            raise ValueError("Choose 'estimator' from values ['first_reach', 'dummy']!")