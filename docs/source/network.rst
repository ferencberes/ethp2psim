.. _network_sect:
Peer-to-peer (P2P) network
==========================

How to create a P2P network?
----------------------------

In this module, we provide two generators to assign weights to the nodes and edges of the peer-to-peer (P2P) network. By our terminology, edge weights represent communication latency on the channels (edges) of the P2P network, while node weights account for node relevance.

.. autoclass:: ethp2psim.network.NodeWeightGenerator
   :members:
   :inherited-members:

.. autoclass:: ethp2psim.network.EdgeWeightGenerator
   :members:
   :inherited-members:

Using these generators, we can initialize the P2P network that is a random regular graph by default but you can also specify any custom graph as input. All network related actions are accessed through the :class:`network.Network` object.

.. autoclass:: ethp2psim.network.Network
   :members:
   :inherited-members:

Using real-world data
---------------------

In our experiments, we compare the random regular graph model for simulating transactions with the underlying structure of the Goerli testnet. It is a good example on how to implement and add benchmark graph datasets to the experiments.
   
.. autoclass:: ethp2psim.data.GoerliTestnet
   :members:
   :inherited-members:

As a summary, let's observe how to mimic the structure and properties of the real world Ethereum P2P network by incorporating

#. staked Ethereum values as node relevance
#. normal distribution of channel latencies
#. structure of the Goerli testnet

.. code-block:: python

  nw_gen = NodeWeightGenerator('stake')
  ew_gen = EdgeWeightGenerator('normal')
  goerli = GoerliTestnet()
  net = Network(nw_gen, ew_gen, graph=goerli.graph)
  
Next, let's discuss how to propagate messages over the P2P network using different message passing protocols.