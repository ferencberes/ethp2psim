# Quickstart

Here, we show an example of how to simulate the [Dandelion protocol](https://arxiv.org/pdf/1701.04439.pdf) in the case of the most basic adversarial strategy (predict a node to be the message source if malicious nodes first heard of this message from the given node).


## Initialize simulation components

```python
from ethp2psim.network import Network, EdgeWeightGenerator, NodeWeightGenerator
from ethp2psim.protocols import DandelionProtocol
from ethp2psim.adversary import DandelionAdversary
```

For reproducibility, **fix a random seed**:

```python
seed = 42
```

First, initialize re-usable **generators for edge and node weights**, e.g., 
   * Edge weihts: weights on edges represent message-spreading latencies. Channel latency can be sampled uniformly at random or from other user-defined distributions.
   * Node weights: nodes might have weights proportional to their staked Ether amount.
   
```python
ew_gen = EdgeWeightGenerator("normal", seed=seed)
nw_gen = NodeWeightGenerator("stake", seed=seed)
```

With these generators, let's create a random 20 regular graph with 100 nodes to be the **peer-to-peer (P2P) network** in this experiment:
```python
net = Network(nw_gen, ew_gen, num_nodes=100, k=20, seed=seed)
```

Next, initialize the Dandelion **protocol** where 
   * A message is broadcasted with a 40% probability in the stem (anonymity) phase or further propagated on the line graph with a 60% probability.
   * With the `broadcast_mode="sqrt"` the message is only sent to a randomly selected square root of neighbors in the spreading phase.
   
```python
dp = DandelionProtocol(net, 0.4, broadcast_mode="sqrt", seed=seed)
```

You can easily visualize the line (anonymity) graph for the Dandelion protocol:
```python
import matplotlib.pyplot as plt
nx.draw(dp.anonymity_graph, node_size=20)
```

Finally, initialize a passive **adversary** against the Dandelion protocol that controls a random 10% of all nodes.
```python
adv = DandelionAdversary(dp, 0.1, active=False, seed=seed)
```
You could also use an active adversary (by setting `active=True`) that refuse to propagate received messages.

## Run simulation

In this experiment, let's **simulate** 20 random messages for the same P2P network and adversary with the Dandelion protocol.

First, initialize the simulator by setting the protocol, the adversary, the number of simulated messages, and how the message source nodes are sampled.
```python
from ethp2psim.simulator import Simulator
sim = Simulator(adv, num_msg=20, use_node_weights=True, verbose=False, seed=seed)
```
Due to the `use_node_weights=True` setting, source nodes for messages are randomly sampled with respect to their staked Ether amount in accordance with the formerly prepared `NodeWeightGenerator`.

Next, run the simulation:
```python
sim.run()
```

## Evaluate the simulation

**Evaluate** the performance of the adversary's deanonymization power for the given simulation. Here, you can choose different estimators that the adversary uses during its deanonymization process. You can choose from the following adversarial strategies to evaluate your simulation: "first_sent", "first_reach", "dummy". See the following example:
```python
from ethp2psim.simulator import Evaluator
evaluator = Evaluator(sim, estimator="first_sent")
print(evaluator.get_report())
```