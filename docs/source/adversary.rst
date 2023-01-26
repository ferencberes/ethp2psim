Adversarial settings
====================

In our experiments, the main goal of the adversary is to predict the source node for each message sent on the P2P network. To obtain these predictions, it is constantly eavesdroping over network traffic through a fixed set of nodes that are controlled by this entity. In our implementation, you can use the :class:`adversary.Adversary` class to setup an adversary with various capabilities:

#. You can set the **fraction of nodes** that the adversary controls
#. You can explicitly set the most **central nodes** (e.g., highest degree, PageRank or Betwenness) to be adversaries. Intuitively, central nodes are reached by messages faster than nodes on the periphery.
#. You can set an adversary to be **active** that won't propagate or broadcast messages further. This way you can test the resilience of different protocols against malicious nodes that refuse to comply with the pre-defined rules of message spreading. 

Node selection
--------------

See the examples below on how to select adversarial nodes uniformly at random or by network centrality.

.. autoclass:: adversary.Adversary


Predict message sources
-----------------------

Next, let's observe how to query the adversary for possible message sources.

.. autofunction:: adversary.Adversary.predict_msg_source

Finally, we introduce the :class:`adversary.EavesdropEvent` class that is used within the :class:`adversary.Adversary` to store information observed by the adversary.

.. autoclass:: adversary.EavesdropEvent
   
So far, we have mostly shown how to interact with only one :class:`message.Message`. But you can only gain meaningful insights by simulation various messages at once. In the next section, we show how to do this with ease.