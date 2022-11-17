import sys, os
import networkx as nx
sys.path.insert(0, '%s/python' % os.getcwd())
from simulator import Simulator, Evaluator
from network import Network
from protocols import BroadcastProtocol, DandelionProtocol
from adversary import Adversary

def test_dummy():
    net = Network(10, 2, node_weight="random")
    protocol = BroadcastProtocol(net)
    adv = Adversary(net, 0.334)
    sim = Simulator(protocol, adv, 3)
    assert sim.protocol.network.num_nodes == 10
    assert len(sim.messages) == 3
    
def test_simulator():
    net = Network(100, 3, node_weight="random")
    adv = Adversary(net, 0.334)
    protocol = BroadcastProtocol(net)
    sim = Simulator(protocol, adv, 1)
    sim.run(0.9)
    assert (len(sim.messages[0].history) / net.num_nodes) >= 0.9
    
def test_simulator_with_max_trials():
    num_nodes = 10
    G = nx.Graph()
    # 2 circles - not weakly connected
    G.add_edges_from([(0,1),(1,2),(2,0),(3,4),(4,5),(5,3)])
    nx.path_graph(num_nodes)
    net = Network(graph=G, node_weight="random")
    adv = Adversary(net, 0.1)
    protocol = DandelionProtocol(net, 0.1)
    sim = Simulator(protocol, adv, 1)
    # test if simulation stops after not reaching more nodes
    sim.run(1.0, max_trials=3)
    assert len(sim.messages[0].history) < num_nodes
    
def test_evaluator():
    num_msg = 50
    net = Network(500, 3, node_weight="random")
    adv = Adversary(net, 0.1)
    protocol = BroadcastProtocol(net)
    sim = Simulator(protocol, adv, num_msg, True)
    sim.run(0.9)
    evaluator = Evaluator(sim)
    results = [evaluator.exact_hits, evaluator.ranks, evaluator.inverse_ranks, evaluator.entropies]
    for res in results:
        assert len(res) == num_msg
    assert len(evaluator.get_report()) == 5