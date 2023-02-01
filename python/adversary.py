import pandas as pd
import numpy as np
import networkx as nx
from protocols import ProtocolEvent, Protocol, DandelionProtocol
from network import Network
from typing import Optional, NoReturn, Iterable, Union, List


class EavesdropEvent:
    """
    Information related to the observed message

    Parameters
    ----------
    node : str
        Message identifier
    source : int
        Source node of the message
    protocol_event : protocols.ProtocolEvent
        Contains message spreading related information

    Examples
    --------
    In this small triangle graph, the triangle inequality does hold for the manually set channel latencies. That is why the message originating from node 1 reaches node 3 (the adversary) faster through node 2.

    >>> from network import *
    >>> from message import Message
    >>> from protocols import BroadcastProtocol
    >>> from adversary import Adversary
    >>> G = nx.DiGraph()
    >>> G.add_nodes_from([1, 2, 3])
    >>> G.add_weighted_edges_from([(1, 2, 0.9), (1, 3, 1.84), (2, 3, 0.85)], weight="latency")
    >>> net = Network(NodeWeightGenerator("random"), EdgeWeightGenerator("custom"), graph=G)
    >>> protocol = BroadcastProtocol(net, "all", seed=44)
    >>> adv = Adversary(protocol, adversaries=[3])
    >>> msg = Message(1)
    >>> for _ in range(3):
    ...    _ = msg.process(adv)
    >>> msg.flush_queue(adv)
    >>> # message reached node 3 from both nodes 1 and 2
    >>> len(adv.captured_events)
    2
    >>> # message reached node 3 faster through node 2 (1.75 ms)
    >>> adv.captured_events[0].protocol_event
    ProtocolEvent(2, 3, 1.750000, 2, True, None)
    >>> # message reached node 3 slower from node 1 (1.84 ms)
    >>> adv.captured_events[1].protocol_event
    ProtocolEvent(1, 3, 1.840000, 1, True, None)
    """

    def __init__(self, mid: str, source: int, pe: ProtocolEvent):
        self.mid = mid
        self.source = source
        self.protocol_event = pe

    @property
    def sender(self) -> int:
        return self.protocol_event.sender

    @property
    def receiver(self) -> int:
        return self.protocol_event.receiver

    def __repr__(self):
        return "EavesdropEvent(%s, %i, %s)" % (
            self.mid,
            self.source,
            self.protocol_event,
        )


class Adversary:
    """
    Abstraction for the entity that tries to deanonymize Ethereum addresses by observing p2p network traffic

    Parameters
    ----------
    protocol : protocol.Protocol
        protocol that determines the rules of message passing
    ratio : float
        Fraction of adversary nodes in the P2P network
    active : bool
        Turn on to enable adversary nodes to deny message propagation
    adversaries: List[int]
        Optional list of nodes that can be set to be adversaries instead of randomly selecting them.
    seed: int (optional)
        Random seed (disabled by default)

    Examples
    --------
    The simplest ways to select nodes controlled by the adversary is to randomly sample a given fraction (e.g, 20%) from all nodes.

    >>> from network import *
    >>> from protocols import BroadcastProtocol
    >>> from adversary import Adversary
    >>> nw_gen = NodeWeightGenerator('stake')
    >>> ew_gen = EdgeWeightGenerator('normal')
    >>> net = Network(nw_gen, ew_gen, 10, 3)
    >>> protocol = BroadcastProtocol(net, broadcast_mode='all')
    >>> adversary = Adversary(protocol, 0.2)
    >>> len(adversary.nodes)
    2

    Another possible approach is to manually set adversarial nodes. For example, you can choose to set nodes with the highest degrees.

    >>> from network import *
    >>> from protocols import BroadcastProtocol
    >>> from adversary import Adversary
    >>> seed = 42
    >>> G = nx.barabasi_albert_graph(20, 3, seed=seed)
    >>> nw_gen = NodeWeightGenerator('stake')
    >>> ew_gen = EdgeWeightGenerator('normal')
    >>> net = Network(nw_gen, ew_gen, graph=G, seed=seed)
    >>> adv_nodes = net.get_central_nodes(4, 'degree')
    >>> protocol = BroadcastProtocol(net, broadcast_mode='all', seed=seed)
    >>> adversary = Adversary(protocol, adversaries=adv_nodes, seed=seed)
    >>> adversary.nodes
    [5, 0, 4, 6]
    """

    def __init__(
        self,
        protocol: Protocol,
        ratio: float = 0.1,
        active: bool = False,
        adversaries: Optional[List[int]] = None,
        seed: Optional[int] = None,
    ):
        self._rng = np.random.default_rng(seed)
        self.ratio = ratio
        self.protocol = protocol
        self.active = active
        self.captured_events = []
        self.captured_msgs = set()
        self._sample_adversary_nodes(self.network, adversaries)

    def __repr__(self):
        return "Adversary(ratio=%.2f, active=%s)" % (
            self.ratio,
            self.active,
        )

    @property
    def network(self):
        return self.protocol.network

    @property
    def candidates(self) -> list:
        return list(self.network.graph.nodes())

    def _sample_adversary_nodes(
        self, network: Network, adversaries: Optional[List[int]] = None
    ) -> NoReturn:
        """Randomly select given fraction of nodes to be adversaries unless the user defines the adversarial nodes"""
        if adversaries != None:
            self.nodes = adversaries
            self.ratio = len(adversaries) / len(self.candidates)
        else:
            num_adversaries = int(len(self.candidates) * self.ratio)
            self.nodes = network.sample_random_nodes(
                num_adversaries,
                use_weights=False,
                replace=False,
                rng=self._rng,
            )

    def eavesdrop_msg(self, ee: EavesdropEvent) -> NoReturn:
        """
        Adversary records the observed information.

        Parameters
        ----------
        ee : EavesdropEvent
            EavesdropEvent that the adversary receives

        """
        self.captured_events.append(ee)
        self.captured_msgs.add(ee.mid)

    def _find_first_contact(
        self, estimator: str
    ) -> Iterable[Union[dict, pd.DataFrame]]:
        contact_time = {}
        received_from = {}
        contact_node = {}
        for ee in self.captured_events:
            message_id = ee.mid
            sender = ee.sender
            receiver = ee.receiver
            if estimator == "first_sent":
                timestamp = ee.protocol_event.delay - self.network.get_edge_weight(
                    sender, receiver, self.protocol.anonymity_network
                )
            else:
                timestamp = ee.protocol_event.delay
            if (not message_id in contact_time) or timestamp < contact_time[message_id]:
                contact_time[message_id] = timestamp
                received_from[message_id] = sender
                contact_node[message_id] = receiver
        arr = np.zeros((len(self.captured_msgs), len(self.candidates)))
        empty_predictions = pd.DataFrame(
            arr, columns=self.candidates, index=list(self.captured_msgs)
        )
        return contact_time, contact_node, received_from, empty_predictions

    def _dummy_estimator(self) -> pd.DataFrame:
        N = len(self.candidates) - len(self.nodes)
        arr = np.ones((len(self.captured_msgs), len(self.candidates))) / N
        predictions = pd.DataFrame(
            arr, columns=self.candidates, index=list(self.captured_msgs)
        )
        for node in self.nodes:
            predictions[node] *= 0
        return predictions

    def predict_msg_source(self, estimator: str = "first_reach") -> pd.DataFrame:
        """
        Predict source nodes for each message

        By default, the node from whom the adversary first heard the message is assigned 1.0 probability while every other node receives zero.

        Parameters
        ----------
        estimator : {'first_reach', 'first_sent', 'dummy'}, default 'first_reach'
            Strategy to assign probabilities to network nodes:
            * first_reach: the node from whom the adversary first heard the message is assigned 1.0 probability while every other node receives zero.
            * first_sent: the node that sent the message the earliest to the receiver
            * dummy: the probability is divided equally between non-adversary nodes.

        Examples
        --------
        In this small triangle graph, the triangle inequality does hold for the manually set channel latencies. That is why the adversary node 3 can correctly predicting node 1 to be the message source by using the first sent estimator heuristic.

        >>> from network import *
        >>> from message import Message
        >>> from protocols import BroadcastProtocol
        >>> from adversary import Adversary
        >>> G = nx.DiGraph()
        >>> G.add_nodes_from([1, 2, 3])
        >>> G.add_weighted_edges_from([(1, 2, 0.9), (1, 3, 1.84), (2, 3, 0.85)], weight="latency")
        >>> net = Network(NodeWeightGenerator("random"), EdgeWeightGenerator("custom"), graph=G)
        >>> protocol = BroadcastProtocol(net, "all", seed=44)
        >>> adv = Adversary(protocol, adversaries=[3])
        >>> msg = Message(1)
        >>> for _ in range(3):
        ...    _ = msg.process(adv)
        >>> msg.flush_queue(adv)
        >>> # first reach estimator thinks the message source is node 2 that is not true
        >>> dict(adv.predict_msg_source(estimator='first_reach').iloc[0])
        {1: 0.0, 2: 1.0, 3: 0.0}
        >>> # first sent estimator is correct by saying that node 1 is the message source
        >>> dict(adv.predict_msg_source(estimator='first_sent').iloc[0])
        {1: 1.0, 2: 0.0, 3: 0.0}
        """
        if estimator in ["first_reach", "first_sent"]:
            _, _, received_from, predictions = self._find_first_contact(estimator)
            for mid, node in received_from.items():
                predictions.at[mid, node] = 1.0
            return predictions
        elif estimator == "dummy":
            return self._dummy_estimator()
        else:
            raise ValueError(
                "Choose 'estimator' from values ['first_reach', 'first_sent', 'dummy']!"
            )


class DandelionAdversary(Adversary):
    """
    Abstraction for the entity that tries to deanonymize Ethereum addresses by observing p2p network traffic

    Parameters
    ----------
    protocol : protocol.Protocol
        protocol that determines the rules of message passing
    ratio : float
        Fraction of adversary nodes in the P2P network
    active : bool
        Turn on to enable adversary nodes to deny message propagation
    use_node_weights : bool
        Sample adversary nodes with respect to node weights
    adversaries: List[int]
        Optional list of nodes that can be set to be adversaries instead of randomly selecting them.
    """

    def __init__(
        self,
        protocol: Protocol,
        ratio: float,
        active: bool = False,
        use_node_weights: bool = False,
        adversaries: Optional[List[int]] = None,
    ):
        super(Adversary, self).__init__(
            protocol, ratio, active, use_node_weights, adversaries
        )

    def __repr__(self):
        return "DandelionAdversary(ratio=%.2f, active=%s, use_node_weights=%s)" % (
            self.ratio,
            self.active,
            self.use_node_weights,
        )

    @property
    def network(self):
        return self.protocol.network

    @property
    def candidates(self) -> list:
        return list(self.network.graph.nodes())

    def predict_msg_source(self, protocol: DandelionProtocol) -> pd.DataFrame:
        """
        Predict source nodes for each message in a run of the Dandelion Protocol

        We implement the adversarial strategy against the Dandelion Protocol described by Sharma et al. https://arxiv.org/pdf/2201.11860.pdf See page 5 for a description of the adversary.

        Parameters
        ----------
        dandelionProtocol : The instantiation of the DandelionProtocol that the adversary tries to deanonymize

        """
        probabilities = {}
        for i in self.captured_events:
            if i.mid in probabilities.keys():
                continue
            probabilities[i.mid] = [0 for j in range(protocol.network.num_nodes)]

            heardFromStemmingPhase = []
            firstBroadcaster = -1
            ## Who is the first node that reports to the adversary in the stem phase?
            if (
                not i.protocol_event.spreading_phase
                and len(heardFromStemmingPhase) == 0
                and (i.protocol_event.sender not in self.nodes)
            ):
                heardFromStemmingPhase.append(i.protocol_event.sender)
            ## The first broadcaster the adversary knows about
            if i.protocol_event.spreading_phase and firstBroadcaster == -1:
                firstBroadcaster = i.protocol_event.sender

            shortestPathLength = sys.maxsize
            shortestAdvPath = []
            for k in self.nodes:
                if heardFromStemmingPhase == []:
                    path = nx.shortest_path(
                        protocol.anonymity_graph, k, firstBroadcaster
                    )
                else:
                    path = nx.shortest_path(
                        protocol.anonymity_graph, k, heardFromStemmingPhase[0]
                    )
                if len(path) < shortestPathLength and len(path) != 2:
                    shortestAdvPath = path
                    shortestPathLength = len(path)
            print("First Broadcaster", firstBroadcaster)

            print(shortestAdvPath)
            probSum = 0  # See Equation 2 here: https://arxiv.org/pdf/2201.11860.pdf
            for node in range(shortestPathLength):
                ## The broadcaster node is not the originator, since in Dandelion the message should have at least 1 hop
                ## We also want to exclude adversarial nodes
                if (
                    node != 0
                    and shortestAdvPath[shortestPathLength - node - 1] not in self.nodes
                ):
                    probabilities[i.mid][
                        shortestAdvPath[shortestPathLength - node - 1]
                    ] = pow(protocol.spreading_proba, node)
                    probSum += pow(protocol.spreading_proba, node)

            for j in range(len(probabilities[i.mid])):
                probabilities[i.mid][j] /= probSum
        deanonProbas = pd.DataFrame.from_dict(probabilities, orient="index")
        return deanonProbas
