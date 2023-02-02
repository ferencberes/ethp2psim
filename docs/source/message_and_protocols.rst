.. _protocols_sect:
Message spreading with protocols
================================

Simple messaging
----------------

At the heart of message spreading we have the :class:`ethp2psim.message.Message` class that represents objects traveling on the P2P network (e.g., block proposal, attestation, simple transaction).

To interact with a message, first you need to define the underlying P2P network (:class:`ethp2psim.network.Network`) that was discussed in detail in the previous section.

Then, there are multiple other components that haven't been intorduced so far like protocols (e.g., :class:`ethp2psim.protocols.BroadcastProtocol`, :class:`ethp2psim.protocols.DandelionProtocol`) that defines the exact rules for message passing, or the adversary (:class:`ethp2psim.adversary.Adversary`) that eavesdrop on the network as the message diffuses over the nodes.

Nonetheless, in the examples below, we showcase how a message, originating from node zero, is propagated over the network with simple broadcasts while an adversary is controling 10% of the P2P network by constantly eavesdropping on the messages.

.. automodule:: ethp2psim.message
   :members:
   :inherited-members:
   :show-inheritance:

How protocols work?
-------------------

Message spreading in detail is more technical. We use the :class:`ethp2psim.protocols.ProtocolEvent` class to track how a given message (:class:`ethp2psim.message.Message`) spreads over the nodes of the P2P network (:class:`ethp2psim.network.Network`). This is where we store valuable information (e.g., time delays, number of hops from the message source) that are essential to evaluate the performance of different protocols in obfuscating message sources.

.. autoclass:: ethp2psim.protocols.ProtocolEvent
   :members:
   :inherited-members:
   
Next, let's discuss the major building blocks of message passing protocols. By default, each implemented protocol stores two different graphs for message passing:

#. A **(public) graph for broadcasting** messages. Basically, it is the same P2P network that we initialize with :class:`network.Network` at the begining of each example. We consider this network to be constant in our experiments.
#. An anonimity graph (e.g., line graph in case of Dandelion by Venkatakrishnan et al.) that is used to obfuscate the source of each message. Note that it is also public, but it can change from time to time.

In our work, we suppose that nodes can decide whether a given channel belongs to the anonymity graph or to the broadcast network. Moreover, adversary nodes heavily depend on this information when they predict possible source nodes for a given message.

For example, in :class:`ethp2psim.protocols.BroadcastProtocol`, which is the most simle baseline in this package, there is no anonymity graph. Messages are spreading only on the P2P network.
   
.. autoclass:: ethp2psim.protocols.BroadcastProtocol
   
While for :class:`ethp2psim.protocols.DandelionProtocol`, each message has a stem-phase where the message is only propagated on the underlying line graph. Then, the message enters the spreading phase where it behaves identically to :class:`ethp2psim.protocols.BroadcastProtocol`.
   
.. autoclass:: ethp2psim.protocols.DandelionProtocol
   :members:
   :inherited-members:
   
In :class:`ethp2psim.protocols.DandelionPlusPlusProtocol`, the anonymity graph is an approximate four regular graph suggested by Fanti et al.
   
.. autoclass:: ethp2psim.protocols.DandelionPlusPlusProtocol
   :members:
   :inherited-members:
   
In the next section, we show various ways on how to setup adversary nodes in the P2P network.