import numpy as np
from tqdm.auto import tqdm
from scipy.stats import entropy
from message import Message
from protocols import Protocol, DandelionProtocol
from adversary import Adversary
from network import Network
from typing import Optional, List, Iterable


class Simulator:
    """
    Abstraction to simulate message passing on a P2P network

    Parameters
    ----------
    adversary : adversary.Adversary
        adversary that observe messages in the P2P network
    num_msg : Optional[int] (Default: 10)
        number of messages to simulate
    use_node_weights : bool
        sample message sources with respect to node weights
    messages : Optional[List[Message]]
        Set messages manually
    seed: int (optional)
        Random seed (disabled by default)
    """

    def __init__(
        self,
        adversary: Adversary,
        num_msg: Optional[int] = 10,
        use_node_weights: bool = False,
        messages: Optional[List[Message]] = None,
        seed: Optional[int] = None,
        verbose: bool = False,
    ):
        self._rng = np.random.default_rng(seed)
        if num_msg > 10:
            self.verbose = False
        else:
            self.verbose = verbose
        self.adversary = adversary
        self.use_node_weights = use_node_weights
        if messages != None:
            self._messages = messages
        elif num_msg != None:
            # NOTE: by default adversary nodes don't send messages in the simulation - they only observe
            self._messages = [
                Message(sender)
                for sender in self.adversary.protocol.network.sample_random_nodes(
                    num_msg,
                    replace=True,
                    use_weights=use_node_weights,
                    exclude=self.adversary.nodes,
                    rng=self._rng,
                )
            ]
        else:
            raise ValueError("One of `num_msg` or `messages` should not be None!")
        self._executed = False

    @property
    def messages(self):
        return self._messages

    def run(
        self,
        coverage_threshold: float = 1.0,
        max_trials: int = 100,
        disable_progress_bar: bool = True,
    ) -> list:
        """
        Run simulation

        Parameters
        ----------
        coverage_threshold : float
            stop propagating a message if it reached the given fraction of network nodes
        max_trials : int
            stop propagating a message if it does not reach any new nodes within `max_trials` steps
        """
        coverage_for_messages = []
        for msg in tqdm(self.messages, disable=disable_progress_bar):
            node_coverage = 0.0
            delta = 1.0
            num_trials = 0
            while node_coverage < coverage_threshold and num_trials < max_trials:
                old_node_coverage = node_coverage
                node_coverage, spreading_phase, stop = msg.process(self.adversary)
                if stop:
                    break
                if node_coverage > old_node_coverage:
                    num_trials = 0
                else:
                    num_trials += 1
                if self.verbose:
                    print(msg.mid, node_coverage, num_trials)
            if self.verbose:
                print()
            coverage_for_messages.append(node_coverage)
        self._executed = True
        return coverage_for_messages

    def node_contact_time_quantiles(
        self, q=np.arange(0.1, 1.0, 0.1)
    ) -> Iterable[np.array]:
        """
        Calculate the mean and the standard deviation for first node contact time quantiles

        Parameters
        ----------
        q : list (Default: numpy.arange(0.1, 1.0, 0.1)))
           Node quantiles
        """
        if self._executed:
            contact_time_quantiles = []
            for msg in self.messages:
                first_contact_times = [
                    contasts[0].delay for node, contasts in msg.history.items()
                ]
                contact_time_quantiles.append(list(np.quantile(first_contact_times, q)))
            quantile_mx = np.array(contact_time_quantiles)
            mean_quantiles = np.mean(quantile_mx, axis=0)
            std_quantiles = np.std(quantile_mx, axis=0)
            return (mean_quantiles, std_quantiles)
        else:
            raise RuntimeError(
                "Execute the `run()` function before querying node contact times!"
            )


class Evaluator:
    """
    Measures the deanonymization performance of the adversary for a given simulation

    Parameters
    ----------
    simulator : Simulator
        Specify the simulation to evaluate
    estimator : {'first_reach', 'shortest_path', 'dummy'}, default 'first_reach'
        Define adversary stategy to predict source node for each message:
        * first_reach: the node from whom the adversary first heard the message is assigned 1.0 probability while every other node receives zero.
        * shortest_path: predicted node probability is proportional (inverse distance) to the shortest weighted path length
        * dummy: the probability is divided equally between non-adversary nodes.
    """

    def __init__(self, simulator: Simulator, estimator: str = "first_reach"):
        self.simulator = simulator
        self.estimator = estimator
        self.probas = simulator.adversary.predict_msg_source(estimator=self.estimator)
        # method='first' is used to properly resolve ties for calculating exact hits
        self.proba_ranks = self.probas.rank(axis=1, ascending=False, method="first")

    @property
    def message_spread_ratios(self):
        N = self.simulator.adversary.protocol.network.num_nodes
        return [len(msg.history) / N for msg in self.simulator.messages]

    @property
    def exact_hits(self):
        hits = []
        for msg in self.simulator.messages:
            # adversary might not see every message
            if (
                msg.mid in self.probas.index
                and self.proba_ranks.loc[msg.mid, msg.source] == 1.0
            ):
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
                ranks.append(self.simulator.adversary.protocol.network.num_nodes)
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
        num_nodes = self.simulator.adversary.protocol.network.num_nodes
        rnd_entropy = entropy(1.0 / num_nodes * np.ones(num_nodes), base=2)
        entropies = []
        for msg in self.simulator.messages:
            # adversary might not see every message
            if msg.mid in self.probas.index:
                entropies.append(entropy(self.probas.loc[msg.mid].values, base=2))
            else:
                entropies.append(rnd_entropy)
        return np.array(entropies)

    def get_report(self) -> dict:
        """Calculate mean performance of the adversary for the given simulation"""
        return {
            "estimator": self.estimator,
            "hit_ratio": np.mean(self.exact_hits),
            "inverse_rank": np.mean(self.inverse_ranks),
            "entropy": np.mean(self.entropies),
            "ndcg": np.mean(self.ndcg_scores),
            "message_spread_ratio": np.mean(self.message_spread_ratios),
        }
