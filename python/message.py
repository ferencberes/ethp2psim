import uuid, heapq
from adversary import Adversary, EavesdropEvent
from protocols import Protocol, ProtocolEvent
from typing import Iterable, Union, NoReturn


class Message:
    """
    Abstraction for Ethereum transactions

    Parameters
    ----------
    source : int
        Source node of the message
        
    Examples
    --------
    >>> from network import *
    >>> from protocols import BroadcastProtocol
    >>> from adversary import Adversary
    >>> nw_gen = NodeWeightGenerator('stake')
    >>> ew_gen = EdgeWeightGenerator('normal')
    >>> # random 3 regular graph with 10 nodes
    >>> net = Network(nw_gen, ew_gen, 10, 3)
    >>> protocol = BroadcastProtocol(net, broadcast_mode='all')
    >>> adversary = Adversary(protocol, 0.1)
    >>> # message originating from node 0
    >>> msg = Message(0)
    >>> _ = msg.process(adversary)
    >>> # message was sent to 3 neighbors of node 0
    >>> len(msg.queue)
    3
    """

    def __init__(self, source: int):
        self.mid = uuid.uuid4().hex
        self.source = source
        self.spreading_phase = False
        # we store events when given nodes saw the message
        self.history = {}
        self.broadcasters = set()
        self.queue = [ProtocolEvent(self.source, self.source, 0.0, 0, False, None)]

    def __repr__(self):
        return "Message(%s, %i)" % (self.mid, self.source)

    def _update_history(self, record: EavesdropEvent) -> NoReturn:
        node = record.receiver
        # update message history
        if node not in self.history:
            self.history[node] = []
        self.history[node].append(record)

    def _update_adversary(self, record: EavesdropEvent, adv: Adversary) -> bool:
        propagate = True
        if record.receiver in adv.nodes:
            adv.eavesdrop_msg(EavesdropEvent(self.mid, self.source, record))
            if adv.active:
                propagate = False
        return propagate

    def flush_queue(self, adv: Adversary) -> NoReturn:
        """
        Process every remaining event in the message queue.

        Parameters
        ----------
        adv : adversary.Adversary
            Adversary that records observed messages on the P2P network
            
        Examples
        --------
        This step is important to showcase the true deanonymization power of the adversary as it should get every message ever sent to its nodes in the P2P network. Later, we will see that it has a huge relevance when the adversary tries to predict message sources using the 'first sent' heuristic.
        
        >>> from network import *
        >>> from protocols import BroadcastProtocol
        >>> from adversary import Adversary
        >>> nw_gen = NodeWeightGenerator('stake')
        >>> ew_gen = EdgeWeightGenerator('normal')
        >>> # random 3 regular graph with 10 nodes
        >>> net = Network(nw_gen, ew_gen, 10, 3)
        >>> protocol = BroadcastProtocol(net, broadcast_mode='all')
        >>> adversary = Adversary(protocol, 0.1)
        >>> # message originating from node 0
        >>> msg = Message(0)
        >>> _ = msg.process(adversary)
        >>> # message was sent to 3 neighbors of node 0
        >>> len(msg.queue)
        3
        >>> # empty queue
        >>> msg.flush_queue(adversary)
        >>> len(msg.queue)
        0
        """
        while len(self.queue) > 0:
            # Some running time could be spared if only adversary node related events were flushed
            record = heapq.heappop(self.queue)
            self._update_history(record)
            _ = self._update_adversary(record, adv)

    def process(self, adv: Adversary) -> Iterable[Union[float, bool]]:
        """
        Propagate message based on the adversary. Note that adversary also contains the protocol.

        Parameters
        ----------
        adv : adversary.Adversary
            Adversary that records observed messages on the P2P network
            
        Examples
        --------
        Here, we present the full picture for message propagation. The message is iteratively processed until it reaches the desired fraction of nodes. Flushing the queue of unprocessed messages is still an essential final step.
        
        >>> from network import *
        >>> from protocols import BroadcastProtocol
        >>> from adversary import Adversary
        >>> nw_gen = NodeWeightGenerator('stake')
        >>> ew_gen = EdgeWeightGenerator('normal')
        >>> # random 3 regular graph with 10 nodes
        >>> net = Network(nw_gen, ew_gen, 10, 3)
        >>> protocol = BroadcastProtocol(net, broadcast_mode='all')
        >>> adversary = Adversary(protocol, 0.1)
        >>> # message originating from node 0
        >>> msg = Message(0)
        >>> # propagate message until it reaches all nodes
        >>> stop = False
        >>> node_fraction = 0.0
        >>> while node_fraction < 1.0 and (not stop):
        ...     node_fraction, _, stop = msg.process(adversary)
        >>> msg.flush_queue(adversary)
        >>> # remainging messages must be processed
        >>> len(msg.queue)
        0
        >>> # all nodes were reached
        >>> len(msg.history)
        10
        """
        protocol = adv.protocol
        # stop propagation if every node received the message
        stop = False
        if len(self.history) < protocol.network.num_nodes:
            # pop record with minimum travel time
            if len(self.queue) > 0:
                record = heapq.heappop(self.queue)
                self._update_history(record)
                propagate = self._update_adversary(record, adv)
                # propagate for ordinary nodes or passive (not active) adversaries
                if propagate:
                    new_events, is_spreading = protocol.propagate(record)
                    if is_spreading:
                        self.broadcasters.add(record.receiver)
                    self.spreading_phase = self.spreading_phase or is_spreading
                    for event in new_events:
                        if not (event.receiver in self.broadcasters):
                            # do not send message to node who previously broadcasted it
                            heapq.heappush(self.queue, event)
            else:
                stop = True
        return (
            (len(self.history) / protocol.network.num_nodes),
            self.spreading_phase,
            stop,
        )
