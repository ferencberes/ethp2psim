import sys, os
import networkx as nx

sys.path.insert(0, "%s/python" % os.getcwd())
from simulator import Simulator, Evaluator
from network import Network, NodeWeightGenerator, EdgeWeightGenerator
from protocols import BroadcastProtocol, DandelionProtocol
from adversary import Adversary
from message import Message

SEED = 43

rnd_node_weight = NodeWeightGenerator("random")
rnd_edge_weight = EdgeWeightGenerator("random")


def test_dummy():
    net = Network(rnd_node_weight, rnd_edge_weight, 10, 2)
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    adv = Adversary(net, 0.334)
    sim = Simulator(protocol, adv, 3)
    assert sim.protocol.network.num_nodes == 10
    assert len(sim.messages) == 3


def test_simulator():
    net = Network(rnd_node_weight, rnd_edge_weight, 100, 3)
    adv = Adversary(net, 0.334)
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    sim = Simulator(protocol, adv, 1, verbose=True)
    sim.run(0.9, max_trials=50)
    assert (len(sim.messages[0].history) / net.num_nodes) >= 0.9


def test_simulator_with_max_trials():
    num_nodes = 10
    G = nx.Graph()
    # 2 circles - not weakly connected
    G.add_edges_from([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    net = Network(rnd_node_weight, rnd_edge_weight, graph=G)
    adv = Adversary(net, 0.1)
    protocol = DandelionProtocol(net, 0.1, broadcast_mode="all", seed=SEED)
    sim = Simulator(protocol, adv, 1)
    # test if simulation stops after not reaching more nodes
    sim.run(1.0, max_trials=3)
    assert len(sim.messages[0].history) < num_nodes


def test_contact_time_quantiles():
    G = nx.Graph()
    # 2 circles - not weakly connected
    G.add_weighted_edges_from(
        [(0, 1, 1.0), (1, 2, 2.0), (2, 3, 3.0), (3, 4, 1.0), (4, 5, 1.0), (5, 6, 1.0)],
        weight="latency",
    )
    net = Network(rnd_node_weight, EdgeWeightGenerator("custom"), graph=G)
    adv = Adversary(net, 0.1)
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    sim = Simulator(protocol, adv, messages=[Message(0)])
    # test if simulation stops after not reaching more nodes
    sim.run(1.0)
    mean_contact_times, _ = sim.node_contact_time_quantiles(q=[0.5, 1.0])
    assert len(mean_contact_times) == 2
    assert mean_contact_times[0] == 6
    assert mean_contact_times[1] == 9


def test_evaluators():
    num_msg = 10
    net = Network(
        NodeWeightGenerator("stake"),
        EdgeWeightGenerator("normal"),
        500,
        3,
    )
    adv = Adversary(net, 0.1)
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    sim = Simulator(protocol, adv, num_msg, True)
    sim.run(0.9)
    for estimator in ["first_reach", "first_sent", "shortest_path", "dummy"]:
        evaluator = Evaluator(sim, estimator)
        results = [
            evaluator.exact_hits,
            evaluator.ranks,
            evaluator.inverse_ranks,
            evaluator.entropies,
        ]
        for res in results:
            assert len(res) == num_msg
        assert len(evaluator.get_report()) == 6
