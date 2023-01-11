Peer-to-peer (P2P) network
==========================

In this module, we provide two generators to assign weights to the nodes and edges of the peer-to-peer (P2P) network. By our terminology, edge weights represent communication latency on the channels (edges) of the P2P network, while node weights account for node relevance.

.. autoclass:: network.NodeWeightGenerator
   :members:
   :inherited-members:

.. autoclass:: network.EdgeWeightGenerator
   :members:
   :inherited-members:

Using these generators, we can initialize the P2P network that is a random regular graph by default but you can also specify any custom graph as input. All network related actions are accessed through the :class:`network.Network` object.

.. autoclass:: network.Network
   :members:
   :inherited-members: