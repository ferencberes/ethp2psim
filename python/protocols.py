from network import Network
import numpy as np
import networkx as nx

class ProtocolEvent:
    """Message information propagated through the peer-to-peer network"""
    
    def __init__(self, sender:int, receiver: int, delay: float, hops: int, spreading_phase: bool=False):    
        """
        Parameters
        ----------
        sender: int
            Sender node
        receiver : int
            Receiver node
        delay : float
            Elapsed time since the message source created this message when it reaches the receiver node
        hops : int
            Number of hops from the source to the receiver node
        spreading_phase: bool
            Flag to indicate whether the message entered the spreading phase
        """
        self.sender = sender
        self.receiver = receiver
        self.delay = delay
        self.hops = hops
        self.spreading_phase = spreading_phase
        
    def __lt__(self, other):
        if(self.delay<other.delay):
            return True
        else:
            return False
        
    def __repr__(self):
        return "ProtocolEvent(%i, %i, %f, %i)" % (self.sender, self.receiver, self.delay, self.hops)
        
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
        return ProtocolEvent(sender, receiver, elapsed_time, pe.hops+1, spreading_phase)
        
class BroadcastProtocol(Protocol):
    """Message propagation is only based on broadcasting"""
    def __init__(self, network: Network, broadcast_mode: str=None, seed: int=None):
        """
        Parameters
        ----------
        network : network.Network
            Represent the underlying P2P network used for message passing
        broadcast_mode : str
            Use value 'sqrt' to broadcast the message only to a randomly selected square root of neighbors. Otherwise the message will be sent to every neighbor.
        seed: int (optional)
            Random seed (disabled by default)
        """
        super(BroadcastProtocol, self).__init__(network)
        self.broadcast_mode = broadcast_mode
        self._rng = np.random.default_rng(seed)
        
    def __repr__(self):
        return "BroadcastProtocol(broadcast_mode=%s)" % self.broadcast_mode
    
    def propagate(self, pe: ProtocolEvent):
        """Propagate message based on protocol rules"""
        new_events = []
        forwarder = pe.receiver
        # TODO: exclude neighbors from sampling that have already broadcasted the message...
        neighbors = list(self.network.graph.neighbors(forwarder))
        if self.broadcast_mode == "sqrt":
            receivers = self._rng.choice(neighbors, size=int(np.sqrt(len(neighbors))), replace=False)
        else:
            receivers = neighbors
        for receiver in receivers:
            if receiver != pe.sender:
                new_events.append(self.get_new_event(forwarder, receiver, pe, True))
        return new_events, True

class DandelionProtocol(BroadcastProtocol):
    """Message propagation is first based on an anonymity phase that is followed by a spreading phase"""
    
    def __init__(self, network: Network, spreading_proba: float, broadcast_mode: str=None, seed: int=None):
        """
        Parameters
        ----------
        network : network.Network
            Represent the underlying P2P network used for message passing
        spreading_proba: float
            Probability to end the anonimity phase and start the spreading phase for each message
        broadcast_mode : str
            Use value 'sqrt' to broadcast the message only to a randomly selected square root of neighbors. Otherwise the message will be sent to every neighbor in the spreading phase.
        seed: int (optional)
            Random seed (disabled by default)
        """
        super(DandelionProtocol, self).__init__(network, broadcast_mode, seed)
        if spreading_proba < 0 or 1 < spreading_proba:
            raise ValueError("The value of the spreading probability should be between 0 and 1 (inclusive)!")
        else:
            self.spreading_proba = spreading_proba
        self._outbound_node = {}
        self._inbound_nodes = {}
        # initialize line graph
        self.change_line_graph()
        #self.approximate_line_graph()
        
    def __repr__(self):
        return "DandelionProtocol(%.4f)" % self.spreading_proba
        
    def change_line_graph(self):
        """Initialize or re-initialize line graph used for the anonymity phase of the Dandelion protocol"""
        for node in self.network.graph.nodes():
            neighbors = list(self.network.graph.neighbors(node))
            # avoid short loops if possible
            if node in self._inbound_nodes:
                free_neighbors = np.setdiff1d(neighbors, list(self._inbound_nodes[node]))
                if len(free_neighbors) > 0:
                    neighbors = free_neighbors
            # select outbound node for the line grpah
            selected = self._rng.choice(neighbors)
            self._outbound_node[node] = selected
            # update inbound nodes
            if not selected in self._inbound_nodes:
                self._inbound_nodes[selected] = set()
            self._inbound_nodes[selected].add(node)
            
    def approximate_line_graph(self, k=5):
        """Initialize or re-initialize an approximate line graph used for the anonymity phase of the Dandelion protocol. This is the original algorithm described in the Dandelion paper. Link: https://arxiv.org/pdf/1701.04439.pdf"""
        # This is going to be our line (anonymity) graph
        G = nx.DiGraph()
        G.add_nodes_from(self.network.graph.nodes())
        # k is a paramter of the algorithm
        for node in self.network.graph.nodes():
            # pick k random targets from all nodes-{node}
            selectedTargetNodes = self._rng.sample(self.network.graph.nodes()-node,k)
            # pick the smallest in-degree
            minDegreeNode = 999999
            connectNode = node
            for finalNode in selectedTargetNodes:
                if G.in_degree(finalNode) < minDegreeNode:
                    connectNode = finalNode
                    minDegreeNode = G.in_degree(finalNode)
            # make connection
            G.add_edge(node, connectNode)
        # Feri Question: Is it not a problem that this line graph is not a subset of the original peer-to-peer network?
        return G
            
    @property
    def line_graph(self):
        L = nx.DiGraph()
        for u, v in self._outbound_node.items():
            L.add_edge(u,v)
        return L
        
    def propagate(self, pe: ProtocolEvent):
        """Propagate message based on protocol rules"""
        if pe.spreading_phase or (self._rng.random() < self.spreading_proba):
            return super(DandelionProtocol, self).propagate(pe)
        else:
            node = pe.receiver
            return [self.get_new_event(node, self._outbound_node[node], pe, False)], False