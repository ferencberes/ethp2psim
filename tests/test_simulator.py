import sys, os
sys.path.insert(0, '%s/python' % os.getcwd())
from simulator import Simulator
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