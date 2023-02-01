Simulating Ethereum transactions
================================

At last, you know every component that is essential to simulate the Ethereum P2P network. This is where the fun begins! Let's get familiar with our :class:`simulator.Simulator` and :class:`simulator.Evaluator` that gives you the power to simulate and understand the Ethereum P2P network under various different setups. 

Simulator setups
----------------

You have two key parameters that you can use to design significantly different experiments:

#. Playing with the `use_node_weights` parameter you can decide whether to sample message sources with respect to node weights (defined by :class:`network.NodeWeightGenerator`) or just sample them uniformly at random from the nodes of the P2P network. **We note that adversarial nodes** (stored within the :class:`adversary.Adversary`) **never get sampled to be message sources!** 
#. On the other hand, you can also set message sources manually. This is extremely useful when you want to analyse a specific scenario.

Below, you can find a few examples for these setups.

.. autoclass:: simulator.Simulator
   
Use the following function to simulate the propagation of sampled messages on the P2P network. We note that in this experiment **messages are simulated independently**. During this process we record individual messages as they reach given nodes of the P2P network, including adversarial nodes.
   
.. autofunction:: simulator.Simulator.run

after running the simulator, you can query the mean and standard deviation of spreading time (measured in milliseconds) for all messages when they reached given fraction of the nodes.

.. autofunction:: simulator.Simulator.node_contact_time_quantiles
   
How to evaluate a simulation?
-----------------------------

We designed the :class:`simulator.Evaluator` class to gain meaningful insights related to the deanonymization power of the :class:`adversary.Adversary` and the average message node coverage (fraction of nodes reached by a given :class:`message.Message`).

Using the :class:`simulator.Evaluator` is very straightforward:

#. First, you run your simulator
#. Then, feed it to the :class:`simulator.Evaluator` and specify the estimator that you want to use for deanonymization.
#. Finally, query the report from the evaluator that will be most useful when you want to compare simulations with different network topology, protocol or other setups.
   
.. autoclass:: simulator.Evaluator