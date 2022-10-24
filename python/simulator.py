from components import Network, Message
import numpy as np

class Simulator():
    def __init__(self, num_nodes: int=100, k: int=5, num_msg: int=10):
        self.G = Network(num_nodes, k)
        self.messages = [Message(sender) for sender in np.random.randint(0, num_nodes-1, num_msg)]
        
    def run(self, coverage_threshold: float=0.9):
        for msg in self.messages:
            reached_nodes = 0.0
            while reached_nodes < coverage_threshold:
                reached_nodes = msg.process(self.G)
                print(msg.mid, reached_nodes)
            print()
            
sim = Simulator(500, 5, 10)
sim.run()