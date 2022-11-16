import sys, os
sys.path.insert(0, '%s/python' % os.getcwd())
import networkx as nx
from network import Network
from message import Message
from protocols import BroadcastProtocol, DandelionProtocol
from adversary import Adversary

SEED = 43
G = nx.Graph()
G.add_edges_from([(0,1),(0,2),(0,3),(1,4),(4,5)])

def test_custom_graph():
    net = Network(graph=G, node_weight="random")
    assert net.num_nodes == 6
    assert net.k == -1
    assert len(net.edge_weights) == 5

def test_adversary():
    net = Network(graph=G, seed=SEED, node_weight="random")
    adv = Adversary(net, 1/3)
    assert len(adv.nodes) == 2
    assert 2 in adv.nodes
    assert 3 in adv.nodes
    
def test_broadcast_single_message():
    net = Network(graph=G, seed=SEED, node_weight="random")
    protocol = BroadcastProtocol(net)
    adv = Adversary(net, 1/3)
    # start a message from the middle
    msg = Message(0)
    assert 0 in msg.history
    # 0 broadcasted the message to all its neighbors (1,2,3)
    for node in [1,2,3]:
        node in msg.history
    first_ratio, _ = msg.process(protocol, adv)
    assert (first_ratio - 2/3) < 0.0001
    second_ratio, _ = msg.process(protocol, adv)
    assert 4 in msg.history
    assert (second_ratio - 5/6) < 0.0001
    third_ratio, _ = msg.process(protocol, adv)
    assert 5 in msg.history
    assert third_ratio == 1.0
    assert msg.history[0].hops == 0
    assert msg.history[1].hops == 1
    assert msg.history[2].hops == 1
    assert msg.history[3].hops == 1
    assert msg.history[4].hops == 2
    assert msg.history[5].hops == 3
    # adversary nodes [2,3] both vitness one EavesdropEvent
    assert len(adv.captured_events) == 2
    predictions = adv.predict_msg_source()
    assert predictions.shape[0] == 1
    assert predictions.shape[1] == G.number_of_nodes()
    # adversary nodes [2,3] first receive the message from node 0
    assert predictions.loc[msg.mid, 0] == 1

def test_dandelion_line_graph():
    net = Network(graph=G, node_weight="random")
    protocol = DandelionProtocol(net, 1/3, seed=SEED)
    L = protocol.line_graph
    assert L.number_of_nodes() == net.num_nodes
    assert L.number_of_edges() == net.num_nodes
    
def test_dandelion_single_message():
    H = nx.complete_graph(10)
    net = Network(graph=H, seed=SEED, node_weight="random")
    protocol = DandelionProtocol(net, 1/4, seed=42)
    adv = Adversary(net, 0.2)
    msg = Message(0)
    assert 0 in msg.history
    # broadcast will happen in the 4th round
    for i in range(4):
        ratio, broadcast = msg.process(protocol, adv)
        print(i, ratio, broadcast)
        if i < 3:
            assert (not broadcast)
        else:
            assert broadcast
    assert ratio == 1.0