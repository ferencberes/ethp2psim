Experimental results
====================

Here, we how some of our results that we achieved by running the simulator with various different parameters. But first, let's discover all the tools that we prepared for you to help your experimentation with our package.

Resources for running experiments
---------------------------------

If you want to compare how well the adversary can deanonymize message sources for the :class:`protocols.BroadcastProtocol` and the :class:`protocols.DandelionProtocol` then we recommend you to use our  `Bash script <https://github.com/ferencberes/ethp2psim/blob/main/scripts/run_experiments.sh>`_. that have three parameters:

#. The number of independent trials to use to gain insights. The mean deanonymization performance of the adversary will be reported for these trials.
#. The size of the P2P :class:`network.Network` to simulate. If you set 0, then the script will load the :class:`data.GoerliTestnet`.
#. Specify a centrality measure (e.g., degree, pagerank or betweenness) to measure the :class:`adversary.Adversary` performance when it controls the most central nodes of the network.

For example, run the following commands in parallel to save some execution time:

.. code-block:: bash

bash run_experiments.sh 10 1000
bash run_experiments.sh 10 0
bash run_experiments.sh 10 1000 degree
bash run_experiments.sh 10 0 degree

This way you will be able to compare results based on 10 trials for a random regular graph with 1000 nodes and 50 degree and the underlying graph of the Goerli testnet. Adversary performance will be evaluated for both highest degree and uniform random node sampling settings.

How to visualize results?
-------------------------

We also prepared a  `notebook <https://github.com/ferencberes/ethp2psim/blob/main/Results.ipynb>`_ that you can use to visualie the results.

Soon we will describe our experimental results in more detail.