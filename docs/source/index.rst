.. ethsim documentation master file, created by
   sphinx-quickstart on Fri Nov 18 09:29:11 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ethp2psim's documentation!
=====================================

ethp2psim is a network privacy simulator for the Ethereum peer-to-peer (p2p) network. It allows developers and researchers to implement, test, and evaluate the anonymity and privacy guarantees of various routing protocols (e.g., Dandelion(++)) and custom privacy-enhanced message routing protocols. Issues, PRs, and contributions are welcome! Let's make Ethereum private together!

In this Python package, we release our modular Ethereum transaction simulator to help better understand and compare different message-passing protocols in different adversarial settings.

Our simulator has the following major components that you can use to build up complex simulations or to implement your own message-passing protocol:

#. The underlying peer-to-peer (P2P) network is used for message passing. By default, we use a random regular graph to simulate the Ethereum P2P network, but custom datasets or graphs can be easily integrated as well. For details, see the :ref:`network_sect` section.

#. The protocol defines the exact rules for message passing. In the :ref:`protocols_sect` section, we introduce several baseline protocols that are implemented in our package.

#. The adversary is constantly eavesdropping on network traffic by controlling a subset of the P2P network nodes. Its main goal is to predict the source node for each message.

Follow the :doc:`quickstart` for some introductory examples on how to merge these components into a simulation!

Motivation
----------

To highlight the potential in our simulator, we show the average fraction of messages (y-axis) deanomyzed by the adversary with respect to different factors:

* i.) the fraction of P2P network nodes controlled by the adversary (x-axis)
* ii.) whether adversarial nodes are selected uniformly at random, or they control nodes with the highest degrees (see columns)
* iii.) the network model (see rows) used to simulate the Ethereum P2P network (random regular with 1000 nodes vs. Goerli testnet with approximately 1500 nodes) 
   
..  figure:: ../../figures/passive_adversary_centrality_hit_ratio.png

The results show that using Dandelion(++) the adversary significantly loses from its deanonymization power. Furthermore, in case of real-world Goerli testnet data and high-degree adversarial nodes the simple broadcasting would be a very bad choice as the adversary can easily predict the source node more than 50% of the messages. 

Acknowledgements
----------------

The development of this simulator and our research was funded by the Ethereum Foundation's `Academic Grant Rounds 2022 <https://blog.ethereum.org/2022/07/29/academic-grants-grantee-announce>`_. 
Thank you for your generous support!

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   quickstart
   network
   message_and_protocols
   adversary
   simulator
   experiments
   contributions
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
