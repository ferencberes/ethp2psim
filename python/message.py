import uuid
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
        # TODO: check existence!
        # we store events when given nodes saw the message
        self.queue = [ProtocolEvent(self.source, self.source, 0.0, 0)]
        self.history = {}
        
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
        if len(self.history) < protocol.network.num_nodes:
            # pop record with minimum travel time
            record = self.queue.pop(0)
            receiver = record.receiver
            # update message history
            if receiver not in self.history:
                self.history[receiver] = []
            self.history[receiver].append(record)
            # propagate and adversary actions
            if record.receiver in adv.nodes:
                adv.eavesdrop_msg(EavesdropEvent(self.mid, self.source, record))
            # TODO: adversary can decide later to propagate the message or not..
            new_events, new_phase = protocol.propagate(record)
            self.spreading_phase = self.spreading_phase or new_phase
            # TODO: implement proper priority queue:
            self.queue += new_events
            self.queue = sorted(self.queue, key=lambda x: x.delay, reverse=False)
        return (len(self.history) / protocol.network.num_nodes), self.spreading_phase