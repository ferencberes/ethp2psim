import sys, os, pytest

sys.path.insert(0, "%s/python" % os.getcwd())
import networkx as nx
from network import Network, NodeWeightGenerator, EdgeWeightGenerator
from message import Message
from protocols import BroadcastProtocol, DandelionProtocol, DandelionPlusPlusProtocol
from adversary import Adversary

SEED = 43
G = nx.Graph()
G.add_weighted_edges_from(
    [(0, 1, 0.1), (0, 2, 0.5), (0, 3, 0.15), (1, 4, 0.2), (4, 5, 0.1)], weight="latency"
)

rnd_node_weight = NodeWeightGenerator("random", seed=SEED)
rnd_edge_weight = EdgeWeightGenerator("random", seed=SEED)


def test_invalid_node_weight():
    with pytest.raises(ValueError):
        net = Network(NodeWeightGenerator(None), rnd_edge_weight, graph=G)


def test_invalid_spreading_probability():
    H = nx.complete_graph(10)
    net = Network(
        rnd_node_weight, EdgeWeightGenerator("unweighted"), graph=H, seed=SEED
    )
    with pytest.raises(ValueError):
        protocol = DandelionProtocol(net, -5, seed=42)


def test_invalid_edge_weight():
    with pytest.raises(ValueError):
        net = Network(rnd_node_weight, EdgeWeightGenerator(None), graph=G)


def test_custom_graph():
    for nw in ["random", "stake", "degree", "betweenness"]:
        for ew in ["random", "normal", "unweighted"]:
            net = Network(NodeWeightGenerator(nw), EdgeWeightGenerator(ew), graph=G)
            assert net.num_nodes == 6
            assert net.k == -1
            assert len(net.edge_weights) == 5


def test_graph_update():
    net = Network(NodeWeightGenerator("degree"), EdgeWeightGenerator("custom"), graph=G)
    # node 1 has degree 2
    assert net.node_weights[1] == 2
    H = nx.Graph()
    H.add_weighted_edges_from([(1, 5, 0.9), (5, 6, 0.1), (4, 5, 0.2)], weight="latency")
    net.update(H, reset_edge_weights=False, reset_node_weights=False)
    assert net.num_nodes == 7
    assert (net.get_edge_weight(1, 5) - 0.9) < 0.0001
    assert (net.get_edge_weight(5, 6) - 0.1) < 0.0001
    assert (net.get_edge_weight(4, 5) - 0.1) < 0.0001
    # node degree weights are always updated despite being `reset_node_weights=False`
    assert net.node_weights[1] == 3


def test_graph_update_with_reset():
    net = Network(rnd_node_weight, EdgeWeightGenerator("custom"), graph=G)
    H = nx.Graph()
    H.add_weighted_edges_from([(4, 5, 0.2)], weight="latency")
    net.update(H, reset_edge_weights=True)
    assert (net.get_edge_weight(4, 5) - 0.2) < 0.0001


def test_graph_edge_removal():
    net = Network(rnd_node_weight, EdgeWeightGenerator("custom"), graph=G)
    assert (net.get_edge_weight(4, 5) - 0.1) < 0.0001
    assert net.remove_edge(5, 4)
    assert not net.remove_edge(0, 5)


def test_sqrt_broadcast_low_degree():
    net_custom = Network(
        rnd_node_weight, EdgeWeightGenerator("custom"), graph=G, seed=SEED
    )
    with pytest.raises(ValueError):
        protocol = BroadcastProtocol(net_custom, seed=SEED, broadcast_mode="sqrt")


def test_broadcast_single_message():
    net_custom = Network(
        rnd_node_weight, EdgeWeightGenerator("custom"), graph=G, seed=SEED
    )
    print(net_custom.edge_weights)
    protocol = BroadcastProtocol(net_custom, broadcast_mode="all", seed=SEED)
    adv = Adversary(protocol, adversaries=[2,3])
    # start a message from the middle
    msg = Message(0)
    receiver_order = [0, 1, 3, 4, 5, 2]
    for i, receiver in enumerate(receiver_order):
        msg.process(adv)
        assert receiver in msg.history
        assert len(msg.history) == i + 1
    assert msg.history[0][0].hops == 0
    assert msg.history[1][0].hops == 1
    assert msg.history[2][0].hops == 1
    assert msg.history[3][0].hops == 1
    assert msg.history[4][0].hops == 2
    assert msg.history[5][0].hops == 3
    # adversary nodes [2,3] both vitness one EavesdropEvent
    assert len(adv.captured_events) == 2
    predictions = adv.predict_msg_source(estimator="first_reach")
    assert predictions.shape[0] == 1
    assert predictions.shape[1] == G.number_of_nodes()
    # adversary nodes [2,3] first receive the message from node 0
    assert predictions.loc[msg.mid, 0] == 1


def test_dummy_adversary():
    net = Network(rnd_node_weight, rnd_edge_weight, graph=G, seed=SEED)
    protocol = BroadcastProtocol(net, broadcast_mode="all", seed=SEED)
    adv = Adversary(protocol, adversaries=[2,3])
    # start a message from the middle
    msg = Message(0)
    msg.process(adv)
    msg.process(adv)
    msg.process(adv)
    # test dummy estimator
    predictions = adv.predict_msg_source(estimator="dummy")
    print(predictions)
    for node in range(5):
        if node in [2, 3]:
            assert predictions.iloc[0][node] == 0.0
        else:
            assert predictions.iloc[0][node] == 0.25


def test_dandelion_line_graph():
    net = Network(rnd_node_weight, rnd_edge_weight, graph=G)
    protocol = DandelionProtocol(net, 1 / 3, broadcast_mode="all", seed=SEED)
    AG = protocol.anonymity_graph
    assert AG.number_of_nodes() == net.num_nodes
    assert AG.number_of_edges() == net.num_nodes


def test_dandelion_pp_line_graph():
    net = Network(rnd_node_weight, rnd_edge_weight, graph=G)
    protocol = DandelionPlusPlusProtocol(net, 1 / 3, broadcast_mode="all", seed=SEED)
    AG = protocol.anonymity_graph
    assert AG.number_of_nodes() == net.num_nodes
    assert AG.number_of_edges() == 2 * net.num_nodes


def test_dandelion_single_message():
    H = nx.complete_graph(10)
    net = Network(
        rnd_node_weight, EdgeWeightGenerator("unweighted"), graph=H, seed=SEED
    )
    protocol = DandelionProtocol(net, 1 / 4, broadcast_mode="all", seed=SEED+1)
    #print(protocol.anonymity_graph.edges())
    adv = Adversary(protocol)
    msg = Message(0)
    # broadcast will happen in the 5th step
    for i in range(13):
        #print(msg.queue)
        ratio, broadcast, _ = msg.process(adv)
        print(i, ratio, broadcast)
        if i < 6:
            assert not broadcast
        else:
            assert broadcast
    assert ratio == 1.0


def test_dandelion_pp_single_message():
    H = nx.complete_graph(10)
    net = Network(
        rnd_node_weight, EdgeWeightGenerator("unweighted"), graph=H, seed=SEED
    )
    protocol = DandelionPlusPlusProtocol(net, 1 / 4, broadcast_mode="all", seed=SEED+2)
    adv = Adversary(protocol)
    msg = Message(0)
    # broadcast will happen in the 4th step
    for i in range(13):
        ratio, broadcast, _ = msg.process(adv)
        print(i, ratio, broadcast)
        if i < 3:
            assert not broadcast
        else:
            assert broadcast
    assert ratio == 1.0
