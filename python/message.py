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
    """

    def __init__(self, source: int):
        self.mid = uuid.uuid4().hex
        self.source = source
        self.spreading_phase = False
        # we store events when given nodes saw the message
        self.history = {}
        self.broadcasters = set()
        self.queue = [ProtocolEvent(self.source, self.source, 0.0, 0)]

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
        Process every remaining event in the message queue
        
        Parameters
        ----------
        adv : adversary.Adversary
            Adversary that records observed messages on the P2P network
        """
        while len(self.queue) > 0:
            # Some running time could be spared if only adversary node related events were flushed
            record = heapq.heappop(self.queue)
            self._update_history(record)
            _ = self._update_adversary(record, adv)

    def process(
        self, protocol: Protocol, adv: Adversary
    ) -> Iterable[Union[float, bool]]:
        """
        Propagate message based on the given protocol

        Parameters
        ----------
        protocol : protocols.Protocol
            Protocol that defines message spreading
        adv : adversary.Adversary
            Adversary that records observed messages on the P2P network
        """
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
                self.flush_queue(adv)
                stop = True
        return (
            (len(self.history) / protocol.network.num_nodes),
            self.spreading_phase,
            stop,
        )
