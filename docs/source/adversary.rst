Adversarial settings
====================

In our experiments, the main goal of the adversary is to predict the source node for each message sent on the P2P network. The adversary is constantly eavesdropping on network traffic through a fixed set of nodes controlled by this entity to obtain these predictions. In our implementation, you can use the :class:`adversary.Adversary` class to set up an adversary with various capabilities:

#. You can set the **fraction of nodes** that the adversary controls.
#. You can explicitly set the most **central nodes** (e.g., nodes with the highest degree, PageRank or Betweenness centrality) to be adversaries. Intuitively, central nodes are reached by messages faster than nodes on the periphery.
#. You can set an adversary to be **active** that won't propagate or broadcast messages further. This way, you can test the resilience of different protocols against malicious nodes that refuse to comply with the pre-defined rules of message spreading.
#. You can choose from various protocol-specific adversaries (e.g., :class:`ethp2psim.adversary.DandelionAdversary` ) that are more efficient than the baseline methods.
 
Node selection
--------------

See the examples below on how to select adversarial nodes uniformly at random or by network centrality.

.. autoclass:: ethp2psim.adversary.Adversary


Predict message sources
-----------------------

Next, let's observe how to query the adversary for possible message sources.

.. autofunction:: ethp2psim.adversary.Adversary.predict_msg_source

Finally, we introduce the :class:`ethp2psim.adversary.EavesdropEvent` class that is used within the :class:`ethp2psim.adversary.Adversary` to store information observed by the adversary.

.. autoclass:: ethp2psim.adversary.EavesdropEvent
   
So far, we have mostly shown how to interact with only one :class:`ethp2psim.message.Message`. But you can only gain meaningful insights by simulating various messages at once. In the next section, we show how to do this with ease.