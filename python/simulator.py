from components import *
import numpy as np

class Simulator():
    def __init__(self, protocol: Protocol, adv: Adversary, num_msg: int=10, verbose=True):
        self.verbose = verbose
        self.protocol = protocol
        self.adversary = adv
        self.messages = [Message(sender) for sender in np.random.randint(0, self.protocol.network.num_nodes-1, num_msg)]
        
    def run(self, coverage_threshold: float=0.9):
        for msg in self.messages:
            reached_nodes = 0.0
            while reached_nodes < coverage_threshold:
                reached_nodes = msg.process(self.protocol, self.adversary)
                if self.verbose:
                    print(msg.mid, reached_nodes)
            if self.verbose:
                print()