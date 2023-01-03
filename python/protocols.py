from network import Network
import numpy as np
import networkx as nx

class ProtocolEvent:
    """
    Message information propagated through the peer-to-peer network
        
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
    
    def __init__(self, sender:int, receiver: int, delay: float, hops: int, spreading_phase: bool=False):    
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
        elapsed_time = pe.delay + self.network.get_edge_weight(sender, receiver)
        return ProtocolEvent(sender, receiver, elapsed_time, pe.hops+1, spreading_phase)
        
class BroadcastProtocol(Protocol):
    """
    Message propagation is only based on broadcasting
       
    Parameters
    ----------
    network : network.Network
        Represent the underlying P2P network used for message passing
    broadcast_mode : str
        Use value 'sqrt' to broadcast the message only to a randomly selected square root of neighbors. Otherwise the message will be sent to every neighbor.
    seed: int (optional)
        Random seed (disabled by default)
    """
    
    def __init__(self, network: Network, broadcast_mode: str=None, seed: int=None):
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
    """
    Message propagation is first based on an anonymity phase that is followed by a spreading phase
        
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
    
    def __init__(self, network: Network, spreading_proba: float, broadcast_mode: str=None, seed: int=None):
        super(DandelionProtocol, self).__init__(network, broadcast_mode, seed)
        if spreading_proba < 0 or 1 < spreading_proba:
            raise ValueError("The value of the spreading probability should be between 0 and 1 (inclusive)!")
        else:
            self.spreading_proba = spreading_proba
        # initialize line graph
        self.change_anonimity_graph()
        
    def __repr__(self):
        return "DandelionProtocol(spreading_proba=%.4f, broadcast_mode=%s)" % (self.spreading_proba, self.broadcast_mode)
        
    def change_anonimity_graph(self):
        """Initialize or re-initialize anonymity graph for the anonymity phase of the Dandelion++ protocol"""
        self.anonymity_graph = self._approximate_anonymity_graph()
        self.network.update(self.anonymity_graph)
            
    def _approximate_anonymity_graph(self):
        """Approximate line graph used for the anonymity phase of the Dandelion protocol. This is the original algorithm described in the Dandelion paper. Link: https://arxiv.org/pdf/1701.04439.pdf
        """
        # parameter of the algorithm
        k=3
        # This is going to be our line (anonymity) graph
        LG = nx.DiGraph()
        LG.add_nodes_from(self.network.graph.nodes())
        # k is a paramter of the algorithm
        for node in self.network.nodes:
            # pick k random targets from all nodes-{node}
            candidates = self.network.sample_random_nodes(k, replace=False, exclude=[node])
            # pick the smallest in-degree
            connectNode = candidates[0]
            connectNodeDegree = LG.in_degree(connectNode)
            for candidate in candidates[1:]:
                if LG.in_degree(candidate) < connectNodeDegree:
                    connectNode = candidate
                    connectNodeDegree = LG.in_degree(connectNode)
            # make connection (latency generation is handled in network.Network.update())
            LG.add_edge(node, connectNode)
        return LG
            
    def propagate(self, pe: ProtocolEvent):
        """Propagate message based on protocol rules"""
        if pe.spreading_phase or (self._rng.random() < self.spreading_proba):
            return super(DandelionProtocol, self).propagate(pe)
        else:
            node = pe.receiver
            anonimity_graph_neighbors = [neigh for neigh in self.anonymity_graph.neighbors(node)]
            #assert len(anonimity_graph_neighbors) == 1
            return [self.get_new_event(node, anonimity_graph_neighbors[0], pe, False)], False
        
class DandelionPlusPlusProtocol(DandelionProtocol):
    """
    Message propagation is first based on an anonymity phase that is followed by a spreading phase
        
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
    
    def __init__(self, network: Network, spreading_proba: float, broadcast_mode: str=None, seed: int=None):
        super(DandelionPlusPlusProtocol, self).__init__(network, spreading_proba, broadcast_mode, seed)
        
    def __repr__(self):
        return "DandelionPlusPlusProtocol(spreading_proba=%.4f, broadcast_mode=%s)" % (self.spreading_proba, self.broadcast_mode)
    
    def _approximate_anonymity_graph(self):
        """Approximates a directed 4-regular graph in a fully-distributed fashion. See Algorithm 2 in the original Dandelion++ paper https://arxiv.org/pdf/1805.11060.pdf"""
        # This is going to be our anonymity graph
        AG = nx.DiGraph()
        AG.add_nodes_from(self.network.nodes)
        for node in self.network.nodes:
            # pick 2 random targets from all nodes-{node}
            candidates = self.network.sample_random_nodes(2, replace=False, exclude=[node])
            # make connections with the two selected nodes (latency generation is handled in network.Network.update())
            for candidate in candidates:
                AG.add_edge(node, candidate)
        return AG
    
    def propagate(self, pe: ProtocolEvent):
        """Propagate messages based on the Dandelion++ protocol rules. See Algorithm 5 in the original Dandelion++ paper. Link: https://arxiv.org/pdf/1805.11060.pdf"""
        if pe.spreading_phase or (self._rng.random() < self.spreading_proba):
            return BroadcastProtocol.propagate(self, pe)
        else:
            node = pe.receiver
            #Randomly select the recipient of the message among the neighbors in the anonymity graph
            anonimity_graph_neighbors = [neigh for neigh in self.anonymity_graph.neighbors(node)]
            receiver_node = self._rng.choice(anonimity_graph_neighbors, size=1)[0]
            return [self.get_new_event(node, receiver_node, pe, False)], False