import sys, os
import networkx as nx

sys.path.insert(0, "%s/python" % os.getcwd())
from simulator import Simulator, Evaluator
from network import Network, NodeWeightGenerator, EdgeWeightGenerator
from protocols import BroadcastProtocol, DandelionProtocol
from adversary import Adversary
from message import Message
from experiments import *

SEED = 43

rnd_node_weight = NodeWeightGenerator("random", seed=SEED)
rnd_edge_weight = EdgeWeightGenerator("random", seed=SEED)


def test_dummy():
    net = Network(rnd_node_weight, rnd_edge_weight, 10, 2)
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    adv = Adversary(protocol, 0.334)
    sim = Simulator(adv, 3)
    assert sim.adversary.protocol.network.num_nodes == 10
    assert len(sim.messages) == 3


def test_simulator():
    net = Network(rnd_node_weight, rnd_edge_weight, 100, 3)
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    adv = Adversary(protocol, 0.334)
    sim = Simulator(adv, 1, verbose=True)
    sim.run(0.9, max_trials=50)
    assert (len(sim.messages[0].history) / net.num_nodes) >= 0.9


def test_simulator_with_max_trials():
    num_nodes = 10
    G = nx.Graph()
    # 2 circles - not weakly connected
    G.add_edges_from([(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3)])
    net = Network(rnd_node_weight, rnd_edge_weight, graph=G)
    protocol = DandelionProtocol(net, 0.1, broadcast_mode="all", seed=SEED)
    adv = Adversary(protocol, 0.1)
    sim = Simulator(adv, 1)
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
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    adv = Adversary(protocol, 0.1)
    sim = Simulator(adv, messages=[Message(0)])
    # test if simulation stops after not reaching more nodes
    sim.run(1.0)
    mean_contact_times, _ = sim.node_contact_time_quantiles(q=[0.5, 1.0])
    assert len(mean_contact_times) == 2
    assert mean_contact_times[0] == 6
    assert mean_contact_times[1] == 9


"""#tmp disable
def test_evaluators_with_random_seed():
    seed = 42
    num_msg = 10
    net = Network(
        NodeWeightGenerator("random"), EdgeWeightGenerator("normal"), 100, 20, seed=seed
    )
    dp = DandelionProtocol(net, 0.5, seed=seed)
    adv = Adversary(dp, 0.1, seed=seed)
    sim = Simulator(adv, num_msg, seed=seed, verbose=False)
    sim.run()
    reports = {}
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
        reports[estimator] = evaluator.get_report()
        assert len(reports[estimator]) == 6
    # due to fixing random seeds the results are reproducible
    assert (reports["first_reach"]["ndcg"] - 0.2907) < 0.0001
    assert (reports["first_sent"]["ndcg"] - 0.3606) < 0.0001
    assert (reports["dummy"]["ndcg"] - 0.2180) < 0.0001
"""


def test_first_reach_vs_first_sent():
    G = nx.DiGraph()
    G.add_nodes_from([1, 2, 3])
    G.add_weighted_edges_from(
        [(1, 2, 0.9), (1, 3, 1.84), (2, 3, 0.85)], weight="latency"
    )

    net = Network(rnd_node_weight, EdgeWeightGenerator("custom"), graph=G)
    protocol = BroadcastProtocol(net, "all", seed=44)
    adv = Adversary(protocol, ratio=0.0, adversaries=[3])
    sim = Simulator(adv, 1, messages=[Message(1)])

    assert 3 in sim.adversary.nodes
    assert len(sim.messages) == 1

    new_reports = run_and_eval(sim)

    sim.messages[0].flush_queue(sim.adversary)

    print(new_reports)
    assert sim.adversary.predict_msg_source("first_sent").iloc[0][1] == 1
    assert sim.adversary.predict_msg_source("first_reach").iloc[0][2] == 1
