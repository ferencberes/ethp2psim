import sys, os
sys.path.insert(0, '%s/python' % os.getcwd())
import networkx as nx
from components import Network, Message, BroadcastProtocol, Adversary

def test_custom_graph():
    G = nx.Graph()
    G.add_edges_from([(0,1),(0,2),(0,3),(1,4),(4,5)])
    net = Network(graph=G)
    assert net.num_nodes == 6
    assert net.k == -1
    assert len(net.weights) == 5
    
def test_single_message():
    G = nx.Graph()
    G.add_edges_from([(0,1),(0,2),(0,3),(1,4),(4,5)])
    net = Network(graph=G)
    protocol = BroadcastProtocol(net)
    # start a message from the middle
    msg = Message(0)
    adv = Adversary(net, 0.334)
    first_ratio = msg.process(protocol, adv)
    assert (first_ratio - 2/3) < 0.0001
    second_ratio = msg.process(protocol, adv)
    assert (second_ratio - 5/6) < 0.0001
    third_ratio = msg.process(protocol, adv)
    assert third_ratio == 1.0
    assert msg.history[0].hops == 0
    assert msg.history[1].hops == 1
    assert msg.history[2].hops == 1
    assert msg.history[3].hops == 1
    assert msg.history[4].hops == 2
    assert msg.history[5].hops == 3
    
def test_adversary():
    G = nx.Graph()
    G.add_edges_from([(0,1),(0,2),(0,3),(1,4),(4,5)])
    net = Network(graph=G)
    adv = Adversary(net, 0.334, seed=42)
    assert  1 <= len(adv.nodes)