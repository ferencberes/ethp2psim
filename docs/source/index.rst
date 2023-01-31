.. ethsim documentation master file, created by
   sphinx-quickstart on Fri Nov 18 09:29:11 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ethp2psim's documentation!
==================================

In this Python package, we release our modular Ethereum transaction simulator to help better understand and compare different message passing protocols in different adversarial settings.

Our simulator has the following major components that you can use to build up complex simulations or to implement your own message passing protocol:

#. The underlying peer-to-peer (P2P) network used for message passing. By default, we use random regular graph to simulate the Ethereum P2P network, but custom datasets or graphs can be easily integrated as well. For details see the :ref:`network_sect` section.

#. The protocol that defines the exact rules for message passing. In the :ref:`protocols_sect` section, we intorduce several baseline protocols that are implemented in our package.

#. The adversary that is constantly eavesdropping over network traffic by controlling a subset of the P2P network nodes. Its main goal is to predict the source node for each message.

Follow the :doc:`quickstart` for some introdunctionary examples on how to merge these components into a simulation!

To highlight the potential in our simulator, we show the average fraction of messages (y-axis) deanomyzed by the adversary with respect to different factors:

* i.) the fraction of P2P network nodes controlled by the adversary (x-axis)
* ii.) whether adversarial nodes are selected uniformly at random or they control nodes with the highest degrees (see columns)
* iii.) the network model (see rows) used to simulate the Ethereum P2P network (random regular with 1000 nodes vs. Goerli testnet with approximately 1500 nodes) 

.. image:: https://info.ilab.sztaki.hu/~fberes/ethp2psim/figures/passive_adversary_centrality_hit_ratio.png
   :width: 1000

The results show that using Dandelion(++) the adversary significantly loses from its deanonymization power. Furthermore, in case of real-world Goerli testnet data and high-degree adversarial nodes the simple broadcasting would be a very bad choice as the adversary can easily predict the source node more than 50% of the messages. 

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   quickstart
   network
   message_and_protocols
   adversary
   simulator
   contributions
   acknowledgements

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
