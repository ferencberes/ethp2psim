import sys, os
sys.path.insert(0, '%s/python' % os.getcwd())
import networkx as nx
from network import Network
from message import Message
from protocols import BroadcastProtocol
from adversary import Adversary

G = nx.Graph()
G.add_edges_from([(0,1),(0,2),(0,3),(1,4),(4,5)])

def test_custom_graph():
    net = Network(graph=G)
    assert net.num_nodes == 6
    assert net.k == -1
    assert len(net.weights) == 5

def test_adversary():
    net = Network(graph=G)
    adv = Adversary(net, 1/3, seed=42)
    assert len(adv.nodes) == 2
    assert 4 in adv.nodes
    assert 5 in adv.nodes
    
def test_single_message():
    net = Network(graph=G)
    protocol = BroadcastProtocol(net)
    # start a message from the middle
    msg = Message(0)
    adv = Adversary(net, 1/3, seed=42)
    first_ratio, _ = msg.process(protocol, adv)
    assert (first_ratio - 2/3) < 0.0001
    second_ratio, _ = msg.process(protocol, adv)
    assert (second_ratio - 5/6) < 0.0001
    third_ratio, _ = msg.process(protocol, adv)
    assert third_ratio == 1.0
    assert msg.history[0].hops == 0
    assert msg.history[1].hops == 1
    assert msg.history[2].hops == 1
    assert msg.history[3].hops == 1
    assert msg.history[4].hops == 2
    assert msg.history[5].hops == 3
    # adversary nodes [4,5] both vitness one EavesdropEvent
    print(adv.captured_events)
    assert len(adv.captured_events) == 2
    predictions = adv.predict_msg_source()
    assert predictions.shape[0] == 1
    assert predictions.shape[1] == G.number_of_nodes()
    # adversary nodes [4,5] first receive the message from node 1
    assert predictions.loc[msg.mid, 1] == 1
