from network import Network

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
        pass
        
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