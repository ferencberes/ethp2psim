import sys, os, pytest
sys.path.insert(0, '%s/python' % os.getcwd())
import networkx as nx
from network import Network, NodeWeightGenerator, EdgeWeightGenerator
from message import Message
from protocols import BroadcastProtocol, DandelionProtocol, DandelionPlusPlusProtocol
from adversary import Adversary

SEED = 43
G = nx.Graph()
G.add_weighted_edges_from([(0,1,0.1),(0,2,0.5),(0,3,0.15),(1,4,0.2),(4,5,0.1)], weight="latency")

def test_invalid_node_weight():
    with pytest.raises(ValueError):
        net = Network(graph=G, node_weight_gen=NodeWeightGenerator(None))
        
def test_invalid_spreading_probability():
    with pytest.raises(ValueError):
        H = nx.complete_graph(10)
        net = Network(graph=H, seed=SEED, edge_weight_gen=EdgeWeightGenerator("unweighted"))
        protocol = DandelionProtocol(net, -5, seed=42) 
        
def test_invalid_edge_weight():
    with pytest.raises(ValueError):
        net = Network(graph=G, edge_weight_gen=EdgeWeightGenerator(None))

def test_custom_graph():
    for nw in ["random", "stake"]:
        for ew in ["random", "normal", "unweighted"]:
            net = Network(graph=G, edge_weight_gen=EdgeWeightGenerator(ew), node_weight_gen=NodeWeightGenerator(nw))
            assert net.num_nodes == 6
            assert net.k == -1
            assert len(net.edge_weights) == 5
            
def test_graph_update():
    net = Network(graph=G, edge_weight_gen=EdgeWeightGenerator("custom"))
    H = nx.Graph()
    H.add_weighted_edges_from([(1,5,0.9),(5,6,0.1),(4,5,0.2)], weight="latency")
    net.update(H, reset_edge_weights=False)
    assert net.num_nodes == 7
    assert (net.get_edge_weight(1, 5) - 0.9) < 0.0001
    assert (net.get_edge_weight(5, 6) - 0.1) < 0.0001
    assert (net.get_edge_weight(4, 5) - 0.1) < 0.0001
    
def test_graph_update_with_reset():
    net = Network(graph=G, edge_weight_gen=EdgeWeightGenerator("custom"))
    H = nx.Graph()
    H.add_weighted_edges_from([(4,5,0.2)], weight="latency")
    net.update(H, reset_edge_weights=True)
    assert (net.get_edge_weight(4, 5) - 0.2) < 0.0001
    
def test_graph_edge_removal():
    net = Network(graph=G, edge_weight_gen=EdgeWeightGenerator("custom"))
    assert (net.get_edge_weight(4, 5) - 0.1) < 0.0001
    assert net.remove_edge(5, 4)
    assert not net.remove_edge(0, 5)

def test_broadcast_single_message():
    net_custom = Network(graph=G, seed=SEED, edge_weight_gen=EdgeWeightGenerator("custom"))
    print(net_custom.edge_weights)
    protocol = BroadcastProtocol(net_custom, seed=SEED)
    adv = Adversary(net_custom, 1/3)
    assert 2 in adv.nodes
    assert 3 in adv.nodes
    # start a message from the middle
    msg = Message(0)
    receiver_order = [0,1,3,4,5,2]
    for i, receiver in enumerate(receiver_order):
        msg.process(protocol, adv)
        assert receiver in msg.history
        assert len(msg.history) == i+1
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
    net = Network(graph=G, seed=SEED)
    protocol = BroadcastProtocol(net, seed=SEED)
    adv = Adversary(net, 1/3)
    # start a message from the middle
    msg = Message(0)
    msg.process(protocol, adv)
    msg.process(protocol, adv)
    msg.process(protocol, adv)
    # test dummy estimator
    predictions = adv.predict_msg_source(estimator="dummy")
    print(predictions)
    for node in range(5):
        if node in [2,3]:
            assert predictions.iloc[0][node] == 0.0
        else:
            assert predictions.iloc[0][node] == 0.25

def test_dandelion_line_graph():
    net = Network(graph=G)
    protocol = DandelionProtocol(net, 1/3, seed=SEED)
    AG = protocol.anonymity_graph
    assert AG.number_of_nodes() == net.num_nodes
    assert AG.number_of_edges() == net.num_nodes
    
def test_dandelion_pp_line_graph():
    net = Network(graph=G)
    protocol = DandelionPlusPlusProtocol(net, 1/3, seed=SEED)
    AG = protocol.anonymity_graph
    assert AG.number_of_nodes() == net.num_nodes
    assert AG.number_of_edges() == 2 * net.num_nodes
    
def test_dandelion_single_message():
    H = nx.complete_graph(10)
    net = Network(graph=H, seed=SEED, edge_weight_gen=EdgeWeightGenerator("unweighted"))
    protocol = DandelionProtocol(net, 1/4, seed=SEED)
    adv = Adversary(net, 0.2)
    msg = Message(0)
    # broadcast will happen in the 2nd step
    for i in range(11):
        ratio, broadcast, _ = msg.process(protocol, adv)
        print(i, ratio, broadcast)
        if i < 1:
            assert (not broadcast)
        else:
            assert broadcast
    assert ratio == 1.0
    
def test_dandelion_pp_single_message():
    H = nx.complete_graph(10)
    net = Network(graph=H, seed=SEED, edge_weight_gen=EdgeWeightGenerator("unweighted"))
    protocol = DandelionPlusPlusProtocol(net, 1/4, seed=SEED)
    adv = Adversary(net, 0.2)
    msg = Message(0)
    # broadcast will happen in the 2nd step
    for i in range(11):
        ratio, broadcast, _ = msg.process(protocol, adv)
        print(i, ratio, broadcast)
        if i < 1:
            assert (not broadcast)
        else:
            assert broadcast
    assert ratio == 1.0
