import sys
sys.path.insert(0, '../python')
from simulator import Simulator

def test_dummy():
    sim = Simulator(10, 2, 3)
    assert sim.G.num_nodes == 10
    assert len(sim.messages) == 3
    
def test_simulator():
    sim = Simulator(100, 3, 1, verbose=False)
    sim.run(0.9)
    assert (len(sim.messages[0].history) / 100) >= 0.9