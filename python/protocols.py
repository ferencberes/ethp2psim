from network import Network
import numpy as np

class ProtocolEvent:
    """Message information propagated through the peer-to-peer network"""
    
    def __init__(self, node: int, delay: float, hops: int, spreading_phase: bool=False):    
        """
        Parameters
        ----------
        node : int
            Receiver node
        delay : float
            Elapsed time since the message source created this message
        hops : int
            Number of hops from the source to the receiver node
        spreading_phase: bool
            Flag to indicate whether the message entered the spreading phase
        """
        self.node = node
        self.delay = delay
        self.hops = hops
        self.spreading_phase = spreading_phase
        
    def __repr__(self):
        return "ProtocolEvent(%i, %f, %i)" % (self.node, self.delay, self.hops)
        
class Protocol:
    """Abstraction for different message passing protocols"""
    
    def __init__(self, network: Network):
        self.network = network
        
    def propagate(self, pe: ProtocolEvent):
        """Propagate message based on protocol rules"""
        pass
    
    def get_new_event(self, sender: int, receiver: int, pe: ProtocolEvent, spreading_phase: bool):
        """
        Calculate parameters for the propagated message
        
        Parameters
        ----------
        sender : int
            Sender node of the message
        receiver : int
            Receiver node of the message
        pe : ProtocolEvent
            Message parameters at sender node
        spreading_phase : float
            Set whether the spreading phase starts at the receiver node
        """
        link = (sender, receiver)
        if not link in self.network.edge_weights:
            link = (receiver, sender)
        elapsed_time = pe.delay + self.network.edge_weights[link]
        return ProtocolEvent(receiver, elapsed_time, pe.hops+1, spreading_phase)
        
class BroadcastProtocol(Protocol):
    """Transaction propagation is only based on broadcasting"""
    def __init__(self, network: Network):
        """
        Parameters
        ----------
        network : network.Network
            Represent the underlying P2P network used for message passing
        """
        super(BroadcastProtocol, self).__init__(network)
    
    def propagate(self, pe: ProtocolEvent):
        """Propagate message based on protocol rules"""
        new_events = []
        sender = pe.node
        for receiver in self.network.graph.neighbors(sender):
            new_events.append(self.get_new_event(sender, receiver, pe, True))
        return new_events, True

class DandelionProtocol(BroadcastProtocol):
    """Transaction propagation first based on an anonymity phase that is followed by a spreading phase"""
    
    def __init__(self, network: Network, spreading_proba: float, seed: int=None):
        """
        Parameters
        ----------
        network : network.Network
            Represent the underlying P2P network used for message passing
        spreading_proba: float
            Probability to end the anonimity phase and start the spreading phase for each message
        seed: int (optional)
            Random seed (disabled by default)
        """
        super(DandelionProtocol, self).__init__(network)
        self._seed = seed
        self.spreading_proba = spreading_proba
        self.outbound_node = {}
        # initialize line graph
        self.change_line_graph()
        
    def change_line_graph(self):
        """Initialize or re-initialize line graph used for the anonymity phase of the Dandelion protocol"""
        for node in self.network.graph.nodes():
            neighbors = list(self.network.graph.neighbors(node))
            i = np.random.randint(0,len(neighbors))
            self.outbound_node[node] = neighbors[i]
        
    def propagate(self, pe: ProtocolEvent):
        """Propagate message based on protocol rules"""
        if self._seed != None:
            np.random.seed(self._seed)
        if pe.spreading_phase or np.random.random() < self.spreading_proba:
            return super(DandelionProtocol, self).propagate(pe)
        else:
            return [self.get_new_event(pe.node, self.outbound_node[pe.node], pe, False)], False