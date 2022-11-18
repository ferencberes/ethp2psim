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
        self.history = {source:ProtocolEvent(self.source, 0.0, 0)}
        self.queue = [source]
        
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
            new_queue = []
            spreading_phase = False
            for sender in self.queue:
                new_events, spreading_phase_update = protocol.propagate(self.history[sender])
                spreading_phase = spreading_phase or spreading_phase_update 
                for rec in new_events:
                    receiver = rec.node
                    if not receiver in self.history:
                        self.history[receiver] = rec
                        new_queue.append(receiver)
                        # adversary only records first message contact
                        if receiver in adv.nodes:
                            adv.eavesdrop_msg(EavesdropEvent(self.mid, self.source, sender, rec))
            self.queue = new_queue
            self.spreading_phase = spreading_phase
        return (len(self.history) / protocol.network.num_nodes), self.spreading_phase