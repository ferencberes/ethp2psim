# ethsim

[![CI for Ubuntu with Codecov sync](https://github.com/ferencberes/ethsim/actions/workflows/ubuntu.yml/badge.svg)](https://github.com/ferencberes/ethsim/actions/workflows/ubuntu.yml)
[![CI for MacOS without Codecov sync](https://github.com/ferencberes/ethsim/actions/workflows/macos.yml/badge.svg)](https://github.com/ferencberes/ethsim/actions/workflows/macos.yml)
[![codecov](https://codecov.io/gh/ferencberes/ethsim/branch/main/graph/badge.svg?token=6871LSZKSK)](https://codecov.io/gh/ferencberes/ethsim)

## Installation

Create your conda environment:
```bash
conda create -n ethsim python=3.8
```

Activate your environment, then install Python dependencies:
```bash
conda activate ethsim
pip install -r requirements.txt
```

## Tests

Run the following command at the root folder before pushing new commits to the repository!
```bash
pytest --cov
```

## Quickstart

Here, we show an example on how to run a simulation with the Dandelion protocol in case of the most basic adversarial setting (predict a node to be the message source if adversarial nodes first heard of this message from the given node).


Import simulation components:
```python
import sys
sys.path.insert(0, "python")
from network import Network
from protocols import DandelionProtocol
from adversary import Adversary
from simulator import Simulation, Evaluator
```

Initialize a random 4 regular graph with 20 nodes to be the peer-to-peer (P2P):
```python
net = Network(20, 4)
```

Initialize the protocal and draw the related line graph:
```python
import matplotlib.pyplot as plt

dp = DandelionProtocol(net, 0.1)
nx.draw(dp.line_graph, node_size=20)
```

Initilaize adversary nodes (uniform random 10% of all nodes):
```python
adv = Adversary(net, 0.1)
```

Simulate 10 random messages of the P2P network with Dandelion protocol:
```python
sim = Simulator(dp, adv, 10, verbose=False)
sim.run(coverage_threshold=0.9)
```
**NOTE: By default every message is only simulated until it reaches 90% of all nodes**

Evaluate the performance of the adversary for the given simulation:
```python
evaluator = Evaluator(sim)
print(evaluator.get_report())
```

For a more complex experimental setting see the related [notebook](Experimental.ipynb)

## Documentation

Install every dependency that is needed to generate code documentation.
The commands below need to be executed only one:

```bash
cd docs
pip install -r requirements.txt
˙```

Then, you can update code documentation locally with the following command:
```bash
cd docs
make html
```

A generated documentation resides in the `docs/build/html/` folder.