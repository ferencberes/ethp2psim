import numpy as np
from message import Message 
from protocols import Protocol
from adversary import Adversary

class Simulator():
    """Abstraction to simulate message passing on a P2P network"""
    
    def __init__(self, protocol: Protocol, adv: Adversary, num_msg: int=10, verbose=True):
        """
        Parameters
        ----------
        protocol : protocol.Protocol
            protocol that determines the rules of message passing
        adv : adversary.Adversary
            adversary that observe messages in the P2P network
        num_msg : int
            number of messages to simulate
        """
        self.verbose = verbose
        self.protocol = protocol
        self.adversary = adv
        self.messages = [Message(sender) for sender in np.random.randint(0, self.protocol.network.num_nodes-1, num_msg)]
        
    def run(self, coverage_threshold: float=0.9, epsilon=0.001):
        """
        Run simulation
        
        Parameters
        ----------
        coverage_threshold : float
            stop propagating a message if it reached the given fraction of network nodes
        epsilon : adversary.Adversary
            stop propagating a message if it is in the spreading phase and could not reach more than epsilon fraction of network nodes in the previous step
        """
        for msg in self.messages:
            reached_nodes = 0.0
            delta = 1.0
            while reached_nodes < coverage_threshold and delta >= epsilon:
                old_reached_nodes = reached_nodes
                reached_nodes, spreading_phase = msg.process(self.protocol, self.adversary)
                if spreading_phase and old_reached_nodes >= reached_nodes:
                    delta = old_reached_nodes - reached_nodes
                if self.verbose:
                    print(msg.mid, reached_nodes, delta)
            if self.verbose:
                print()