import numpy as np
from tqdm.auto import tqdm
from scipy.stats import entropy
from message import Message 
from protocols import Protocol
from adversary import Adversary

class Simulator():
    """Abstraction to simulate message passing on a P2P network"""
    
    def __init__(self, protocol: Protocol, adv: Adversary, num_msg: int=10, use_weights: bool=False, verbose=True):
        """
        Parameters
        ----------
        protocol : protocol.Protocol
            protocol that determines the rules of message passing
        adv : adversary.Adversary
            adversary that observe messages in the P2P network
        num_msg : int
            number of messages to simulate
        use_weights : int
            sample message sources with respect to node weights
        """
        if num_msg > 10:
            self.verbose = False
        else:
            self.verbose = verbose
        self.protocol = protocol
        self.adversary = adv
        self.use_weights = use_weights
        # adversary nodes don't send messages in the simulation - they only observe
        self.messages = [Message(sender) for sender in self.protocol.network.sample_random_nodes(num_msg, replace=True, use_weights=use_weights, exclude=self.adversary.nodes)]
        
    def run(self, coverage_threshold: float=0.9, max_trials=5, disable_progress_bar=True):
        """
        Run simulation
        
        Parameters
        ----------
        coverage_threshold : float
            stop propagating a message if it reached the given fraction of network nodes
        max_trials : int
            stop propagating a message if it does not reach any new nodes within `max_trials` steps
        """
        for msg in tqdm(self.messages, disable=disable_progress_bar):
            reached_nodes = 0.0
            delta = 1.0
            num_trials = 0
            while reached_nodes < coverage_threshold and num_trials < max_trials:
                old_reached_nodes = reached_nodes
                reached_nodes, spreading_phase = msg.process(self.protocol, self.adversary)
                if reached_nodes > old_reached_nodes:
                    num_trials = 0
                else:
                    num_trials += 1
                if self.verbose:
                    print(msg.mid, reached_nodes, num_trials)
            if self.verbose:
                print()
                

class Evaluator:
    """Measures the deanonymization performance of the adversary for a given simulation"""
    
    def __init__(self, simulator: Simulator, estimator: str="first_reach"):
        """
        Parameters
        ----------
        simulator : Simulator
            Specify the simulation for evaluation
        """
        self.simulator = simulator
        self.estimator = estimator
        self.probas = simulator.adversary.predict_msg_source(estimator=self.estimator)
        # method='first' is used to properly resolve ties for calculating exact hits
        self.proba_ranks = self.probas.rank(axis=1, ascending=False, method="first")
    
    @property
    def message_spread_ratios(self):
        N = self.simulator.protocol.network.num_nodes
        return [len(msg.history) / N for msg in self.simulator.messages]
    
    @property
    def exact_hits(self):
        hits = []
        for msg in self.simulator.messages:
            # adversary might not see every message
            if msg.mid in self.probas.index and self.proba_ranks.loc[msg.mid, msg.source] == 1.0:
                hits.append(1.0)
            else:
                hits.append(0.0)
        return np.array(hits)
    
    @property
    def ranks(self):
        ranks = []
        for msg in self.simulator.messages:
            # adversary might not see every message
            if msg.mid in self.probas.index:
                ranks.append(self.proba_ranks.loc[msg.mid, msg.source])
            else:
                # what to do with unseen messages? random rank might be better...
                ranks.append(self.simulator.protocol.network.num_nodes)
        return np.array(ranks)
    
    @property
    def inverse_ranks(self):
        return 1.0 / self.ranks
    
    @property
    def ndcg_scores(self):
        scores = []
        for msg in self.simulator.messages:
            # adversary might not see every message
            if msg.mid in self.probas.index:
                ndcg = 1.0 / np.log2(1.0 + self.proba_ranks.loc[msg.mid, msg.source])
                scores.append(ndcg)
            else:
                # what to do with unseen messages? random rank might be better...
                scores.append(0.0)
        return np.array(scores)
        
    @property
    def entropies(self):
        num_nodes = self.simulator.protocol.network.num_nodes
        rnd_entropy = entropy(1.0/num_nodes * np.ones(num_nodes))
        entropies = []
        for msg in self.simulator.messages:
            # adversary might not see every message
            if msg.mid in self.probas.index:
                entropies.append(entropy(self.probas.loc[msg.mid].values))
            else:
                entropies.append(rnd_entropy)
        return np.array(entropies)
    
    def get_report(self):
        return {
            "estimator":self.estimator,
            "hit_ratio":np.mean(self.exact_hits),
            "inverse_rank":np.mean(self.inverse_ranks),
            "entropy":np.mean(self.entropies),
            "ndcg":np.mean(self.ndcg_scores),
            "message_spread_ratio":np.mean(self.message_spread_ratios)
        }
        