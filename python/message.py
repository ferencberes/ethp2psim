import uuid, heapq
from adversary import Adversary, EavesdropEvent
from protocols import Protocol, ProtocolEvent
        
class Message:
    """Abstraction for Ethereum transactions"""
    
    def __init__(self, source: int):
        """
        Parameters
        ----------
        source : int
            Source node of the message
        """
        self.mid = uuid.uuid4().hex
        self.source = source
        self.spreading_phase = False
        self.queue = [ProtocolEvent(self.source, self.source, 0.0, 0)]
        # we store events when given nodes saw the message
        self.history = {}
        self.broadcasters = set()
        
    def __repr__(self):
        return "Message(%s, %i)" % (self.mid, self.source)
        
    def process(self, protocol: Protocol, adv: Adversary):
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
                node = record.receiver
                # update message history
                if node not in self.history:
                    self.history[node] = []
                self.history[node].append(record)
                # propagate and adversary actions
                propagate = True
                if node in adv.nodes:
                    adv.eavesdrop_msg(EavesdropEvent(self.mid, self.source, record))
                    if adv.active:
                        propagate = False
                # propagate for ordinary nodes or passive (not active) adversaries
                if propagate:
                    new_events, is_spreading = protocol.propagate(record)
                    if is_spreading:
                        self.broadcasters.add(node)
                    self.spreading_phase = self.spreading_phase or is_spreading
                    for event in new_events:
                        if not (event.receiver in self.broadcasters):
                            # do not send message to node who previously broadcasted it
                            heapq.heappush(self.queue, event)
            else:
                stop = True
        return (len(self.history) / protocol.network.num_nodes), self.spreading_phase, stop