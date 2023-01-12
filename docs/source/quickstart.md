# Quickstart

Here, we show an example of how to simulate the Dandelion protocol in the case of the most basic adversarial setting (predict a node to be the message source if malicious nodes first heard of this message from the given node).


## Initialize simulation components
```python
import sys
sys.path.insert(0, "python")
from network import Network, EdgeWeightGenerator, NodeWeightGenerator
from protocols import DandelionProtocol
from adversary import Adversary
```

First, initialize re-usable **generators for edge and node weights**, e.g. 
   * channel latency is sampled uniformly at random
   * nodes have weights proportional to their staked Ether amount
   
```python
ew_gen = EdgeWeightGenerator("normal")
nw_gen = NodeWeightGenerator("stake")
```

With these generators, let's create a random 4 regular graph with 20 nodes to be the **peer-to-peer (P2P) network** in this experiment:
```python
net = Network(nw_gen, ew_gen, num_nodes=20, k=4)
```

Next, initialize the Dandelion **protocol** where 
   * A message is broadcasted with 40% probability in the stem (anonymity) phase, or it is further propagated on the line graph with 60% probability.  
   * With the `broadcast_mode="sqrt"` the message is only sent to a randomly selected square root of neighbors in the spreading phase.
   
```python
dp = DandelionProtocol(net, 0.4, broadcast_mode="sqrt")
```

You can easily visualize the line (anonymity) graph for the Dandelion protocol:
```python
import matplotlib.pyplot as plt
nx.draw(dp.anonymity_graph, node_size=20)
```

Finally, initilaize a passive **adversary** that controls random 10% of all nodes:
```python
adv = Adversary(net, 0.1, active=False)
```
You could also use an active adversary (by setting `active=True`) that refuse to propagate received messages.

## Run simulation

In this experiment, let's **simulate** 10 random messages for the same P2P network and adversary with the Dandelion protocol.

First, initialize the simulator by setting the protocol, the adversary, the number of simulated messages, and how the message source nodes are sampled.
```python
from simulator import Simulation
sim = Simulator(dp, adv, num_msg=10, use_node_weights=True, verbose=False)
```
Due to the `use_node_weights=True` setting, source nodes for messages are randomly sampled with respect to their staked Ether amount in accordance with the formerly prepared `NodeWeightGenerator`.

Next, run the simulation:
```python
sim.run()
```

## Evaluate the simulation

**Evaluate** the performance of the adversary for the given simulation. Here, you can choose different estimators for adversary performance evaluation (e.g., "first_sent", "first_reach", "dummy"):
```python
from simulator import Evaluator
evaluator = Evaluator(sim, estimator="first_reach")
print(evaluator.get_report())
```