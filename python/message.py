import uuid
from adversary import Adversary, EavesdropEvent
from protocols import Protocol, ProtocolEvent
        
class Message:
    def __init__(self, source: int):
        """Abstraction for Ethereum transactions"""
        self.mid = uuid.uuid4().hex
        self.source = source
        # TODO: check existence!
        self.history = {source:ProtocolEvent(self.source, 0.0, 0)}
        self.queue = [source]
        
    def process(self, protocol: Protocol, adv: Adversary):
        """Propagate message based on rules defined by the given protocol"""
        new_queue = []
        for sender in self.queue:
            new_events = protocol.propagate(self.history[sender])
            for rec in new_events:
                receiver = rec.node
                if not receiver in self.history:
                    self.history[receiver] = rec
                    new_queue.append(receiver)
                    # adversary only records first message contact
                    if receiver in adv.nodes:
                        adv.eavesdrop_msg(EavesdropEvent(self.mid, self.source, sender, rec))
        self.queue = new_queue
        return len(self.history) / protocol.network.num_nodes