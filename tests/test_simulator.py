import sys, os
sys.path.insert(0, '%s/python' % os.getcwd())
from simulator import Simulator
from components import *

def test_dummy():
    net = Network(10, 2)
    protocol = BroadcastProtocol(net)
    sim = Simulator(protocol, 3)
    assert sim.protocol.network.num_nodes == 10
    assert len(sim.messages) == 3
    
def test_simulator():
    net = Network(100, 3)
    protocol = BroadcastProtocol(net)
    sim = Simulator(protocol, 1, verbose=True)
    sim.run(0.9)
    assert (len(sim.messages[0].history) / net.num_nodes) >= 0.9