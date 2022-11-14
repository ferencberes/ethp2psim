import sys, os
sys.path.insert(0, '%s/python' % os.getcwd())
from simulator import Simulator, Evaluator
from network import Network
from protocols import BroadcastProtocol
from adversary import Adversary

def test_dummy():
    net = Network(10, 2)
    protocol = BroadcastProtocol(net)
    adv = Adversary(net, 0.334)
    sim = Simulator(protocol, adv, 3)
    assert sim.protocol.network.num_nodes == 10
    assert len(sim.messages) == 3
    
def test_simulator():
    net = Network(100, 3)
    adv = Adversary(net, 0.334)
    protocol = BroadcastProtocol(net)
    sim = Simulator(protocol, adv, 1, verbose=True)
    sim.run(0.9, 0.0)
    assert (len(sim.messages[0].history) / net.num_nodes) >= 0.9
    
def test_evaluator():
    num_msg = 50
    net = Network(500, 3)
    adv = Adversary(net, 0.1)
    protocol = BroadcastProtocol(net)
    sim = Simulator(protocol, adv, num_msg, True, verbose=True)
    sim.run(0.9, 0.0)
    evaluator = Evaluator(sim)
    results = [evaluator.exact_hits, evaluator.ranks, evaluator.inverse_ranks, evaluator.entropies]
    for res in results:
        assert len(res) == num_msg
    assert len(evaluator.get_report()) == 2