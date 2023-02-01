from network import Network
from adversary import Adversary
from protocols import Protocol
from simulator import Simulator, Evaluator
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List
import pandas as pd
import numpy as np
from tqdm import tqdm

### run experiments ###


def run_and_eval(
    simulator: Simulator,
    coverage_threshold: float = 1.0,
    estimators: list = ["first_reach", "first_sent"],
    q=np.arange(0.1, 1.0, 0.1),
) -> list:
    """
    Run and evaluate simulator

    Parameters
    ----------
    simulator: simulator.Simulator
        Simulator to be executed
    coverage_threshold: float
        Fraction of nodes the messages must reach in the simulation
    estimators: list
        Estimator strategies for the adversary during performance evaluation
    q : list (Default: numpy.arange(0.1, 1.0, 0.1)))
           Node quantiles to calculate contact times

    Examples
    --------
    >>> from network import *
    >>> from protocols import BroadcastProtocol
    >>> from adversary import Adversary
    >>> from simulator import Simulator
    >>> nw_gen = NodeWeightGenerator("random")
    >>> ew_gen = EdgeWeightGenerator("normal")
    >>> net = Network(nw_gen, ew_gen, 50, 5)
    >>> protocol = BroadcastProtocol(net, broadcast_mode="all")
    >>> adversary = Adversary(protocol, 0.1)
    >>> simulator = Simulator(adversary, 10)
    >>> reports = run_and_eval(simulator, q=[0.1,0.2,0.5], estimators=["first_sent"])
    >>> len(reports)
    1
    >>> len(reports[0]["mean_contact_time_quantiles"])
    3
    """
    simulator.run(coverage_threshold=coverage_threshold)
    mean_contact_times, std_contact_times = simulator.node_contact_time_quantiles(q=q)
    reports = []
    for estimator in estimators:
        evaluator = Evaluator(simulator, estimator)
        report = evaluator.get_report()
        report["mean_contact_time_quantiles"] = list(mean_contact_times)
        report["std_contact_time_quantiles"] = list(std_contact_times)
        report["adversary"] = str(simulator.adversary)
        report["protocol"] = str(simulator.adversary.protocol)
        report["network"] = str(simulator.adversary.protocol.network)
        reports.append(report)
    return reports


def run_experiment(
    func: Callable, queries: List[dict], max_workers: int = 1
) -> pd.DataFrame:
    """
    Use this function to run experiments in parallel with various different configurations.

    Parameters
    ----------
    func: Callable
        Provide a custom function to execute multiple times with different parameters
    queries: List[dict]
        List of different configurations to be executed
    max_workers: int
        Maximum number of threads to use during execution

    Examples
    --------
    >>> from network import *
    >>> from protocols import DandelionProtocol
    >>> from adversary import Adversary
    >>> from simulator import Simulator
    >>> def single_experiment(config: dict):
    ...     nw_gen = NodeWeightGenerator("random")
    ...     ew_gen = EdgeWeightGenerator("normal")
    ...     net = Network(nw_gen, ew_gen, 50, 5)
    ...     protocol = DandelionProtocol(net, spreading_proba=config["proba"], broadcast_mode="all")
    ...     adversary = Adversary(protocol, 0.1)
    ...     simulator = Simulator(adversary, 10)
    ...     return run_and_eval(simulator, estimators=["first_sent"])
    >>> probas = [0.5,0.25]
    >>> queries = [{"proba":p} for p in probas]
    >>> results = run_experiment(single_experiment, queries)
    >>> len(results)
    2
    """
    results = []
    if max_workers > 1:
        executor = ThreadPoolExecutor(max_workers=max_workers)
        results = list(tqdm(executor.map(func, queries), total=len(queries)))
        executor.shutdown()
        # for res in pool:
        #    results += res
    else:
        for query in tqdm(queries):
            results += func(query)
    results_df = pd.DataFrame(results)
    return results_df


### postprocess experimental results ###


def shorten_protocol_name(x: str) -> str:
    """
    Use this function to get shorter protocol names that look better for visualization

    Parameters
    ----------
    x: str
        Protocol name

    Examples
    --------
    >>> shorten_protocol_name("BroadcastProtocol(broadcast_mode=sqrt)")
    'Broadcast'
    """
    val = x.replace("Protocol", "").replace("spreading_proba", "p")
    val = val.split("broadcast")[0][:-1].replace("(", ": ")
    if val[-1] == ",":
        val = val[:-1]
    return val


def extract_config_columns(df: pd.DataFrame) -> pd.DataFrame:
    tmp_df = df.copy()
    # extract adversary parameters
    adv_col = "adversary"
    tmp_df["adversary_ratio"] = tmp_df[adv_col].apply(
        lambda x: float(str(x).split("ratio=")[1].split(",")[0])
    )
    # extract protocol parameters
    protocol_col = "protocol"
    tmp_df["broadcast_mode"] = tmp_df[protocol_col].apply(
        lambda x: "sqrt" if "sqrt" in x else "all"
    )
    tmp_df[protocol_col] = tmp_df[protocol_col].apply(shorten_protocol_name)

    return tmp_df


def prepare_results_for_visualization(
    df: pd.DataFrame,
    id_vars: list = [
        "graph_model",
        "protocol",
        "adversary_ratio",
        "adversary_type",
        "adversary_centrality",
        "estimator",
        "broadcast_mode",
    ],
) -> pd.DataFrame:
    return df.drop(["inverse_rank", "entropy"], axis=1).melt(
        value_vars=["hit_ratio", "ndcg", "message_spread_ratio"],
        var_name="metric",
        id_vars=id_vars,
    )
