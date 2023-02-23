import pandas as pd
import numpy as np
import networkx as nx
from .protocols import *
from .network import Network
from typing import Optional, NoReturn, Iterable, Union, List
from collections import deque


class EavesdropEvent:
    """
    Information related to the observed message

    Parameters
    ----------
    node : str
        Node identifier that observed the message
    source : int
        Source node of the message
    protocol_event : protocols.ProtocolEvent
        Contains message spreading related information

    Examples
    --------
    In this small triangle graph, the triangle inequality does hold for the manually set channel latencies. That is why the message originating from node 1 reaches node 3 (the adversary) faster through node 2.

    >>> from .network import *
    >>> from .message import Message
    >>> from .protocols import BroadcastProtocol
    >>> from .adversary import Adversary
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

    >>> from .network import *
    >>> from .protocols import BroadcastProtocol
    >>> from .adversary import Adversary
    >>> nw_gen = NodeWeightGenerator('stake')
    >>> ew_gen = EdgeWeightGenerator('normal')
    >>> net = Network(nw_gen, ew_gen, 10, 3)
    >>> protocol = BroadcastProtocol(net, broadcast_mode='all')
    >>> adversary = Adversary(protocol, 0.2)
    >>> len(adversary.nodes)
    2

    Another possible approach is to manually set adversarial nodes. For example, you can choose to set nodes with the highest degrees.

    >>> from .network import *
    >>> from .protocols import BroadcastProtocol
    >>> from .adversary import Adversary
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
        
    def record_packet(self, pe: ProtocolEvent):
        """Record sent protocol events. Only relevant for OnionRoutingProtocol"""
        pass

    def find_first_contact(
        self, estimator: str
    ) -> Iterable[Union[dict, pd.DataFrame]]:
        contact_time = {}
        reference_time = {}
        received_from = {}
        contact_node = {}
        contact_by_broadcast = {}
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
            if (not message_id in contact_time) or timestamp < reference_time[message_id]:
                reference_time[message_id] = timestamp
                contact_time[message_id] = ee.protocol_event.delay
                received_from[message_id] = sender
                contact_node[message_id] = receiver
                contact_by_broadcast[message_id] = ee.protocol_event.spreading_phase
        arr = np.zeros((len(self.captured_msgs), len(self.candidates)))
        empty_predictions = pd.DataFrame(
            arr, columns=self.candidates, index=list(self.captured_msgs)
        )
        return (
            contact_time,
            contact_node,
            received_from,
            contact_by_broadcast,
            empty_predictions,
        )

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

        >>> from .network import *
        >>> from .message import Message
        >>> from .protocols import BroadcastProtocol
        >>> from .adversary import Adversary
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
            _, _, received_from, _, predictions = self.find_first_contact(estimator)
            for mid, node in received_from.items():
                predictions.at[mid, node] = 1.0
        elif estimator == "dummy":
            predictions = self._dummy_estimator()
        else:
            raise ValueError(
                "Choose 'estimator' from values ['first_reach', 'first_sent', 'dummy']!"
            )
        return predictions.fillna(0.0)


class DandelionAdversary(Adversary):
    """
    Abstraction for the entity that tries to deanonymize Ethereum addresses when message passing is executed with the Dandelion protocol.

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

    References
    ----------
    Shaileshh Bojja Venkatakrishnan, Giulia Fanti, and Pramod Viswanath. 2017. Dandelion: Redesigning the Bitcoin Network for Anonymity. In Proceedings of the 2017 ACM SIGMETRICS / International Conference on Measurement and Modeling of Computer Systems (SIGMETRICS '17 Abstracts). Association for Computing Machinery, New York, NY, USA, 57. https://doi.org/10.1145/3078505.3078528
    """

    def __init__(
        self,
        protocol: Protocol,
        ratio: float = 0.1,
        active: bool = False,
        adversaries: Optional[List[int]] = None,
        seed: Optional[int] = None,
    ):
        if not isinstance(protocol, DandelionProtocol):
            raise ValueError("The given protocol must be a DandelionProtocol!")
        super(DandelionAdversary, self).__init__(
            protocol, ratio, active, adversaries, seed
        )

    def __repr__(self):
        return (
            super(DandelionAdversary, self)
            .__repr__()
            .replace("Adversary", "DandelionAdversary")
        )

    def _find_candidates_on_line_graph(self, start_node: int) -> list:
        G = self.protocol.anonymity_graph.reverse(copy=True)
        q = deque([(start_node, 0)])
        candidates = []
        processed = []
        while len(q) > 0:
            # print(q)
            candidate, weight = q.popleft()
            # do not process loops twice
            if candidate in processed:
                continue
            else:
                processed.append(candidate)
                next_weight = (
                    1.0
                    if weight == 0
                    else weight * (1.0 - self.protocol.spreading_proba)
                )
                if candidate != start_node:
                    candidates.append((candidate, weight))
                for node in G.neighbors(candidate):
                    # if node is not an adversary then add it to the queue
                    if not node in self.nodes:
                        q.append((node, next_weight))
        # print(candidates)
        return candidates

    def predict_msg_source(self, estimator: str = "first_reach") -> pd.DataFrame:
        """
        Predict source nodes for each message in a run of the Dandelion Protocol

        Parameters
        ----------
        estimator : {'first_reach', 'first_sent', 'dummy'}, default 'first_reach'
            Strategy to assign probabilities to network nodes:
            * first_reach: the node from whom the adversary first heard the message is assigned 1.0 probability while every other node receives zero.
            * first_sent: the node that sent the message the earliest to the receiver
            * dummy: the probability is divided equally between non-adversary nodes.

        References
        ----------
        We implement the adversarial strategy against the Dandelion Protocol described by Sharma et al. https://arxiv.org/pdf/2201.11860.pdf See page 5 for a description of the adversary.
        """
        dummy_predictions = self._dummy_estimator()
        if estimator in ["first_reach", "first_sent"]:
            (
                _,
                contact_node,
                received_from,
                contact_by_broadcast,
                predictions,
            ) = self.find_first_contact(estimator)
            for msg in self.captured_msgs:
                # print(msg)
                if contact_by_broadcast[msg]:
                    candidates = self._find_candidates_on_line_graph(received_from[msg])
                else:
                    candidates = self._find_candidates_on_line_graph(contact_node[msg])
                # Candidate list can be empty, when adversary hears the message from a source (i.e., 0 in-degree) node in the anonymity graph. This is an expected behavior. Suppose the first contact node happens to be a source (0 in-degree) in the anonymity graph. In that case, the adversary cannot say anything since it cannot backtrack in the anonymity graph and surely knows that the source node could not be the originator of the message since, in Dandelion(++), there is always at least one hop. This weird scenario can only occur if the adversary hears about the message only in the broadcast phase.
                if len(candidates) > 0:
                    nodes, weights = zip(*candidates)
                    weights = np.array(weights) / np.sum(weights)
                    predictions.loc[msg] = pd.Series(data=weights, index=nodes)
                else:
                    predictions.loc[msg] = dummy_predictions.loc[msg]
        elif estimator == "dummy":
            predictions = dummy_predictions
        else:
            raise ValueError(
                "Choose 'estimator' from values ['first_reach', 'first_sent', 'dummy']!"
            )
        return predictions.fillna(0.0)

class OnionRoutingAdversary(Adversary):
    def __init__(
        self,
        protocol: Protocol,
        ratio: float = 0.1,
        active: bool = False,
        adversaries: Optional[List[int]] = None,
        seed: Optional[int] = None,
    ):
        if not isinstance(protocol, OnionRoutingProtocol):
            raise ValueError("The given protocol must be an OnionRoutingProtocol!")
        super(OnionRoutingAdversary, self).__init__(
            protocol, ratio, active, adversaries, seed
        )
        self.sent_packets = []
        self.received_packets = []
        self.first_broadcaster_events = {} 

    def __repr__(self):
        return (
            super(OnionRoutingAdversary, self)
            .__repr__()
            .replace("Adversary", "OnionRoutingAdversary")
        )
    
    def eavesdrop_msg(self, ee: EavesdropEvent) -> NoReturn:
        """
        Adversary records the observed information.

        Parameters
        ----------
        ee : EavesdropEvent
            EavesdropEvent that the adversary receives

        """
        path_info = ee.protocol_event.path
        if path_info == None:
            self.captured_events.append(ee)
            self.captured_msgs.add(ee.mid)
        else:
            self.received_packets.append(ee.protocol_event)
            # when the adversary node is the broadcaster in the encrypted channel
            if len(path_info) == 1:
                assert path_info[0] in self.nodes
                self.first_broadcaster_events[ee.mid] = ee.protocol_event
    
    def record_packet(self, pe: ProtocolEvent) -> NoReturn:
        """
        Record sent encrypted packages
        
        Parameters
        ----------
        pe : ProtocolEvent
            Event sent by the adversary to the next relayer in the encrypted channel.
        """
        self.sent_packets.append(pe)
        
    def _track_first_broadcaster(self, mid: str, contact_time: dict, contact_node: dict, received_from: dict) -> Iterable[Union[int, float]]:
        """Guess first broadcaster (last relayer in the channel) for a given message based on adversary observations."""
        if mid in self.first_broadcaster_events:
            pe = self.first_broadcaster_events[mid]
            t = pe.delay
            v = pe.receiver
            u = pe.sender
            step = 0
        else:
            t = contact_time[mid]
            v = contact_node[mid]
            u = received_from[mid]
            step = -1
        return (u, v, t, step)
    
    def _find_candidates(self, mid: str, prev_events: list, next_events: list, contact_time: dict, contact_node: dict, received_from: dict, estimator: str) -> List[Iterable[Union[int, float]]]:
        """Try to reconstruct encrypted channels based on received and sent packets information."""
        def step_back(u:int, v:int, t:float, step:int):
            return u, t - self.protocol.network.get_edge_weight(u, v, external=self.protocol.anonymity_network), step+1
        predictions = []
        queue = deque([self._track_first_broadcaster(mid, contact_time, contact_node, received_from)])
        #print(queue)
        while len(queue) > 0:
            u, v, t, step = queue.popleft()
            #print(u, v, t, step)
            v, t, step = step_back(u, v, t, step)
            #print(v, t, step)
            is_adv = v in self.nodes
            #print(is_adv)
            contacts, candidates, timestamps = prev_events if is_adv else next_events
            if timestamps != None:
                idx = (np.abs(np.array(timestamps) - t)).argmin()
                #print('time', t, timestamps, idx, candidates)
                # TODO: how to generalize this condition?
                if np.abs(t-timestamps[idx]) < 1.0: # difference is less than 1ms
                    queue.append((candidates[idx], v, t, step))
                else:
                    predictions.append((v,t,step))
        return predictions
    
    def predict_msg_source(self, estimator: str = "first_reach") -> pd.DataFrame:
        """
        Predict source nodes for each message in a run of the Dandelion Protocol

        Parameters
        ----------
        estimator : {'first_reach', 'first_sent', 'dummy'}, default 'first_reach'
            Strategy to assign probabilities to network nodes:
            * first_reach: the node from whom the adversary first heard the message is assigned 1.0 probability while every other node receives zero.
            * first_sent: the node that sent the message the earliest to the receiver
            * dummy: the probability is divided equally between non-adversary nodes.
        """
        def extract_timeline(packets: List[ProtocolEvent]):
            """Extract received or sent packets timeline for OnionRoutingAdversary"""
            if len(packets) > 0:
                events = [(pe.receiver, pe.sender, pe.delay) for pe in packets]
                out = list(zip(*events))
            else:
                # it can happen that no adversary was in the encrypted channel
                out = [None, None, None]
            return out
        contact_time, contact_node, received_from, _, predictions = self.find_first_contact(estimator)
        next_events = extract_timeline(self.sent_packets)
        prev_events = extract_timeline(self.received_packets)
        #print(next_events)
        #print(prev_events)
        for mid in self.captured_msgs:
            candidates = [record[0] for record in self._find_candidates(mid, prev_events, next_events, contact_time, contact_node, received_from, estimator)]
            if len(candidates) == 0:
                # TODO: later handle that adversaries never start a message
                candidates = self.candidates
                # original source is surely not the assumed first broadcaster
                candidates.remove(received_from[mid])
            for node in candidates:
                predictions.at[mid, node] = 1.0/len(candidates)
        return predictions.fillna(0.0)