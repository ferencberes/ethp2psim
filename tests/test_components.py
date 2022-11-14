import sys, os
sys.path.insert(0, '%s/python' % os.getcwd())
import networkx as nx
from network import Network
from message import Message
from protocols import BroadcastProtocol, DandelionProtocol
from adversary import Adversary

G = nx.Graph()
G.add_edges_from([(0,1),(0,2),(0,3),(1,4),(4,5)])

def test_custom_graph():
    net = Network(graph=G)
    assert net.num_nodes == 6
    assert net.k == -1
    assert len(net.edge_weights) == 5

def test_adversary():
    net = Network(graph=G)
    adv = Adversary(net, 1/3, seed=42)
    assert len(adv.nodes) == 2
    assert 3 in adv.nodes
    assert 4 in adv.nodes
    
def test_broadcast_single_message():
    net = Network(graph=G)
    protocol = BroadcastProtocol(net)
    adv = Adversary(net, 1/3, seed=42)
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
    # adversary nodes [3,4] both vitness one EavesdropEvent
    assert len(adv.captured_events) == 2
    predictions = adv.predict_msg_source()
    assert predictions.shape[0] == 1
    assert predictions.shape[1] == G.number_of_nodes()
    # adversary nodes [3,4] first receive the message from node 0
    assert predictions.loc[msg.mid, 0] == 1

def test_dandelion_single_message():
    net = Network(graph=G)
    protocol = DandelionProtocol(net, 1/3, seed=42)
    adv = Adversary(net, 1/3, seed=42)
    # start a message from the middle
    msg = Message(0)
    assert 0 in msg.history
    first_ratio, first_broadcast = msg.process(protocol, adv)
    print(first_ratio, first_broadcast)
    # node 0 did not boradcast but send the message only to node 2
    assert 2 in msg.history
    assert 1 not in msg.history
    assert 3 not in msg.history
    assert (not first_broadcast)
    # node 2 has no other neighbor than 0 so no additional node get the message
    second_ratio, second_broadcast = msg.process(protocol, adv)
    print(second_broadcast, msg.history)
    assert len(msg.history) == 2
    # TODO: what happens in the upcoming steps?