from .network import Network
import numpy as np
import networkx as nx
from typing import Optional, Iterable, NoReturn, Union


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
    path : list
        Remaining path for the message (only used in TOREnhancedProtocol)


    Examples
    --------
    In a tiny example we show that we record message spreading with ProtocolEvents.

    >>> from .network import *
    >>> from .message import Message
    >>> from .adversary import Adversary
    >>> import networkx as nx
    >>> G = nx.Graph()
    >>> G.add_edges_from([(1,2),(2,3),(1,3)])
    >>> nw_gen = NodeWeightGenerator('stake')
    >>> ew_gen = EdgeWeightGenerator('normal')
    >>> seed = 42
    >>> net = Network(nw_gen, ew_gen, graph=G, seed=seed)
    >>> protocol = BroadcastProtocol(net, broadcast_mode='all', seed=seed)
    >>> adversary = Adversary(protocol, adversaries=[3], seed=seed)
    >>> msg = Message(1)
    >>> for _ in range(3):
    ...    _ = msg.process(adversary)
    >>> msg.flush_queue(adversary)
    >>> # message reached node 2 only from node 1
    >>> msg.history[2]
    [ProtocolEvent(1, 2, 228.034291, 1, True, None)]
    >>> # and it reached node 3 from node 1 and node 3
    >>> msg.history[3]
    [ProtocolEvent(1, 3, 242.482918, 1, True, None), ProtocolEvent(2, 3, 250.755617, 2, True, None)]
    """

    def __init__(
        self,
        sender: int,
        receiver: int,
        delay: float,
        hops: int,
        spreading_phase: bool = False,
        path: list = None,
    ):
        self.sender = sender
        self.receiver = receiver
        self.delay = delay
        self.hops = hops
        self.spreading_phase = spreading_phase
        self.path = path

    def __lt__(self, other):
        if self.delay < other.delay:
            return True
        else:
            return False

    def __repr__(self):
        return "ProtocolEvent(%i, %i, %f, %i, %s, %s)" % (
            self.sender,
            self.receiver,
            self.delay,
            self.hops,
            self.spreading_phase,
            self.path,
        )


class Protocol:
    """Abstraction for different message passing protocols"""

    def __init__(self, network: Network, seed: Optional[int] = None):
        self._rng = np.random.default_rng(seed)
        self._seed = seed
        self.network = network
        self.anonymity_network = None

    @property
    def anonymity_graph(self):
        return None if self.anonymity_network is None else self.anonymity_network.graph

    def change_anonimity_graph(self) -> NoReturn:
        """Initialize or re-initialize anonymity graph for the anonymity phase of Dandelion, Dandelion++ or TOREnhanced protocols"""
        G = self._generate_anonymity_graph()
        self.anonymity_network = Network(
            self.network.node_weight_generator,
            self.network.edge_weight_generator,
            graph=G,
            seed=self._seed,
        )

    def propagate(self, pe: ProtocolEvent):
        """Propagate message based on protocol rules"""
        pass

    def _get_new_event(
        self,
        sender: int,
        receiver: int,
        pe: ProtocolEvent,
        spreading_phase: bool,
        path: list = None,
    ) -> ProtocolEvent:
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
        elapsed_time = pe.delay + self.network.get_edge_weight(
            sender, receiver, self.anonymity_network
        )
        return ProtocolEvent(
            sender, receiver, elapsed_time, pe.hops + 1, spreading_phase, path
        )


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

    Examples
    --------
    The broadcast protocol has no anonymity graph.

    >>> from .network import *
    >>> nw_generator = NodeWeightGenerator("random")
    >>> ew_generator = EdgeWeightGenerator("normal")
    >>> net = Network(nw_generator, ew_generator, num_nodes=10, k=2)
    >>> broadcast = BroadcastProtocol(net, broadcast_mode='all')
    >>> broadcast.anonymity_network is None
    True
    """

    def __init__(
        self, network: Network, broadcast_mode: str = "sqrt", seed: Optional[int] = None
    ):
        super(BroadcastProtocol, self).__init__(network, seed)
        avg_degree = np.mean(list(dict(network.graph.degree()).values()))
        if avg_degree < 9.0 and broadcast_mode == "sqrt":
            raise ValueError(
                "You should not use `broatcast_mode='sqrt'` with average graph degree less than 9! The provided graph has %.1f average degree."
                % avg_degree
            )
        else:
            self.broadcast_mode = broadcast_mode

    def __repr__(self):
        return "BroadcastProtocol(broadcast_mode=%s)" % self.broadcast_mode

    def _generate_anonymity_graph(self) -> nx.Graph:
        raise RuntimeError("Invalid call for BroadcastProtocol!")

    def propagate(self, pe: ProtocolEvent) -> Iterable[Union[list, bool]]:
        """Propagate message based on protocol rules"""
        new_events = []
        forwarder = pe.receiver
        # TODO: exclude neighbors from sampling that have already broadcasted the message... it requires global knowledge so it might not have to be implemented!
        neighbors = list(self.network.graph.neighbors(forwarder))
        if self.broadcast_mode == "sqrt":
            receivers = self._rng.choice(
                neighbors, size=int(np.sqrt(len(neighbors))), replace=False
            )
        else:
            receivers = neighbors
        for receiver in receivers:
            if receiver != pe.sender:
                new_events.append(self._get_new_event(forwarder, receiver, pe, True))
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

    Examples
    --------
    The anonymity graph is a line graph where the number of edges equals to the number of nodes.

    >>> from .network import *
    >>> nw_generator = NodeWeightGenerator("random")
    >>> ew_generator = EdgeWeightGenerator("normal")
    >>> net = Network(nw_generator, ew_generator, num_nodes=10, k=2)
    >>> num_edges = net.graph.number_of_edges()
    >>> dandelion = DandelionProtocol(net, spreading_proba=0.5, broadcast_mode='all')
    >>> dandelion.anonymity_network.num_edges == net.num_nodes
    True

    References
    ----------
    Shaileshh Bojja Venkatakrishnan, Giulia Fanti, and Pramod Viswanath. 2017. Dandelion: Redesigning the Bitcoin Network for Anonymity. In Proceedings of the 2017 ACM SIGMETRICS / International Conference on Measurement and Modeling of Computer Systems (SIGMETRICS '17 Abstracts). Association for Computing Machinery, New York, NY, USA, 57. https://doi.org/10.1145/3078505.3078528
    """

    def __init__(
        self,
        network: Network,
        spreading_proba: float,
        broadcast_mode: str = "sqrt",
        seed: Optional[int] = None,
    ):
        super(DandelionProtocol, self).__init__(network, broadcast_mode, seed)
        if spreading_proba < 0 or 1 < spreading_proba:
            raise ValueError(
                "The value of the spreading probability should be between 0 and 1 (inclusive)!"
            )
        else:
            self.spreading_proba = spreading_proba
        # initialize line graph
        self.change_anonimity_graph()

    def __repr__(self):
        return "DandelionProtocol(spreading_proba=%.4f, broadcast_mode=%s)" % (
            self.spreading_proba,
            self.broadcast_mode,
        )

    def _generate_anonymity_graph(self) -> nx.Graph:
        """Approximate line graph used for the anonymity phase of the Dandelion protocol. This is the original algorithm described in the Dandelion paper. Link: https://arxiv.org/pdf/1701.04439.pdf"""
        # parameter of the algorithm
        k = 3
        # This is going to be our line (anonymity) graph
        LG = nx.DiGraph()
        LG.add_nodes_from(self.network.graph.nodes())
        # k is a paramter of the algorithm
        for node in self.network.nodes:
            # pick k random targets from all nodes-{node}
            candidates = self.network.sample_random_nodes(
                k, replace=False, exclude=[node], rng=self._rng
            )
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

    def propagate(self, pe: ProtocolEvent) -> Iterable[Union[list, bool]]:
        """Propagate message based on protocol rules"""
        flip_coin = 0 < pe.hops
        if pe.spreading_phase or (
            flip_coin and (self._rng.random() < self.spreading_proba)
        ):
            return super(DandelionProtocol, self).propagate(pe)
        else:
            node = pe.receiver
            anonimity_graph_neighbors = [
                neigh for neigh in self.anonymity_graph.neighbors(node)
            ]
            # assert len(anonimity_graph_neighbors) == 1
            return [
                self._get_new_event(node, anonimity_graph_neighbors[0], pe, False)
            ], False


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

    Examples
    --------
    The anonymity graph is an approximate four regular graph.

    >>> from .network import *
    >>> nw_generator = NodeWeightGenerator("random")
    >>> ew_generator = EdgeWeightGenerator("normal")
    >>> net = Network(nw_generator, ew_generator, num_nodes=10, k=2)
    >>> num_edges = net.graph.number_of_edges()
    >>> dandelion_pp = DandelionPlusPlusProtocol(net, spreading_proba=0.5, broadcast_mode='all')
    >>> dandelion_pp.anonymity_network.num_edges == (2 * net.num_nodes)
    True

    References
    ----------
    Giulia Fanti, Shaileshh Bojja Venkatakrishnan, Surya Bakshi, Bradley Denby, Shruti Bhargava, Andrew Miller, and Pramod Viswanath. 2018. Dandelion++: Lightweight Cryptocurrency Networking with Formal Anonymity Guarantees. Proc. ACM Meas. Anal. Comput. Syst. 2, 2, Article 29 (June 2018), 35 pages. https://doi.org/10.1145/3224424
    """

    def __init__(
        self,
        network: Network,
        spreading_proba: float,
        broadcast_mode: str = "sqrt",
        seed: Optional[int] = None,
    ):
        super(DandelionPlusPlusProtocol, self).__init__(
            network, spreading_proba, broadcast_mode, seed
        )

    def __repr__(self):
        return "DandelionPlusPlusProtocol(spreading_proba=%.4f, broadcast_mode=%s)" % (
            self.spreading_proba,
            self.broadcast_mode,
        )

    def _generate_anonymity_graph(self) -> nx.Graph:
        """Approximates a directed 4-regular graph in a fully-distributed fashion. See Algorithm 2 in the Dandelion++ paper."""
        # This is going to be our anonymity graph
        AG = nx.DiGraph()
        AG.add_nodes_from(self.network.nodes)
        for node in self.network.nodes:
            # pick 2 random targets from all nodes-{node}
            candidates = self.network.sample_random_nodes(
                2, replace=False, exclude=[node], rng=self._rng
            )
            # make connections with the two selected nodes (latency generation is handled in network.Network.update())
            for candidate in candidates:
                AG.add_edge(node, candidate)
        return AG

    def propagate(self, pe: ProtocolEvent) -> Iterable[Union[list, bool]]:
        """Propagate messages based on the Dandelion++ protocol rules. See Algorithm 5 in Dandelion++ paper."""
        flip_coin = 0 < pe.hops
        if pe.spreading_phase or (
            flip_coin and (self._rng.random() < self.spreading_proba)
        ):
            return BroadcastProtocol.propagate(self, pe)
        else:
            node = pe.receiver
            # Randomly select the recipient of the message among the neighbors in the anonymity graph
            anonimity_graph_neighbors = [
                neigh for neigh in self.anonymity_graph.neighbors(node)
            ]
            receiver_node = self._rng.choice(anonimity_graph_neighbors, size=1)[0]
            return [self._get_new_event(node, receiver_node, pe, False)], False


class TOREnhancedProtocol(BroadcastProtocol):
    """
    Message propagation is first based on an anonymity phase that is followed by a spreading phase

    Parameters
    ----------
    network : network.Network
        Represent the underlying P2P network used for message passing
    num_arms: int (Default: 1)
        Number of arms for message propagation
    num_hops : int (Default: 2)
        Number of hops (intermediary nodes) on each arm. Intermediary nodes relay the message to the final node on each arm that is the broadcaster node.
    broadcast_mode : str
        Use value 'sqrt' to broadcast the message only to a randomly selected square root of neighbors. Otherwise the message will be sent to every neighbor in the spreading phase.
    seed: int (optional)
        Random seed (disabled by default)

    Examples
    --------
    >>> from .network import *
    >>> nw_generator = NodeWeightGenerator("random")
    >>> ew_generator = EdgeWeightGenerator("normal")
    >>> net = Network(nw_generator, ew_generator, num_nodes=10, k=2)
    >>> num_edges = net.graph.number_of_edges()
    >>> tor = TOREnhancedProtocol(net, num_arms=2, num_hops=3, broadcast_mode='all')
    >>> tor.anonymity_network.num_edges > 2 * net.num_nodes
    True
    """

    def __init__(
        self,
        network: Network,
        num_arms: int = 1,
        num_hops: int = 2,
        broadcast_mode: str = "sqrt",
        seed: Optional[int] = None,
    ):
        super(TOREnhancedProtocol, self).__init__(network, broadcast_mode, seed)
        self.num_arms = num_arms
        self.num_hops = num_hops
        self.change_anonimity_graph()

    def _generate_anonymity_graph(self) -> nx.Graph:
        self.tor_network = {}
        tor_edges = []
        for node in self.network.nodes:
            self.tor_network[node] = []
            for _ in range(self.num_arms):
                arm_nodes = self.network.sample_random_nodes(
                    self.num_hops + 1, replace=False, exclude=[node], rng=self._rng
                )
                self.tor_network[node].append(arm_nodes)
                tor_edges.append((node, arm_nodes[0]))
                for i in range(self.num_hops):
                    tor_edges.append((arm_nodes[i], arm_nodes[i + 1]))
        G = nx.Graph()
        G.add_edges_from(tor_edges)
        return G

    def propagate(self, pe: ProtocolEvent) -> Iterable[Union[list, bool]]:
        """Propagate message based on protocol rules"""
        print(pe)
        if pe.spreading_phase:
            return super(TOREnhancedProtocol, self).propagate(pe)
        else:
            node = pe.receiver
            path = pe.path
            if path is None:
                # message is at starting node: start each arm
                return [
                    self._get_new_event(node, arm[0], pe, False, arm)
                    for arm in self.tor_network[node]
                ], False
            else:
                if len(path) > 1:
                    # intermediary node in the tor network
                    return [
                        self._get_new_event(node, path[1], pe, False, path[1:])
                    ], False
                else:
                    # broadcaster node in the tor network
                    return super(TOREnhancedProtocol, self).propagate(pe)
