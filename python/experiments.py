from network import Network
from adversary import Adversary
from protocols import Protocol
from simulator import Simulator, Evaluator
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List
import pandas as pd
from tqdm import tqdm


def shorten_protocol_name(x: str) -> str:
    val = x.replace("Protocol", "").replace("spreading_proba", "p")
    val = val.split("broadcast")[0][:-1].replace("(", ": ")
    if val[-1] == ",":
        val = val[:-1]
    return val


def shorten_protocol_names_for_df(
    df: pd.DataFrame, col: str = "protocol"
) -> pd.DataFrame:
    tmp_df = df.copy()
    tmp_df[col] = tmp_df[col].apply(shorten_protocol_name)
    return tmp_df


def run_and_eval(
    network: Network,
    adversary: Adversary,
    protocol: Protocol,
    num_msg: int,
    coverage_threshold: float = 1.0,
    estimators: list = ["first_reach", "first_sent"],
) -> list:
    """
    Run and evaluate simulation with the predefined components

    Parameters
    ----------
    network: Network
        P2P network for the experiment
    adversary: Adversary
        Predefined adversary that observes messages during the simulation
    protocol: Protocol
        Predefined message passing protocol
    num_msg: int
        Number of messages to simulate
    coverage_threshold: float
        Fraction of nodes the messages must reach in the simulation
    estimators: list
        Estimator strategies for the adversary during performance evaluation.
    """
    sim = Simulator(protocol, adversary, num_msg, verbose=False)
    sim.run(coverage_threshold=coverage_threshold)
    reports = []
    for estimator in estimators:
        evaluator = Evaluator(sim, estimator)
        report = evaluator.get_report()
        report["protocol"] = str(protocol)
        report["adversary_ratio"] = adversary.ratio
        reports.append(report)
    return reports


def run_experiment(
    func: Callable, queries: List[dict], max_workers: int = 1
) -> pd.DataFrame:
    """
    Use this function to run experiments in parallel.

    Parameters
    ----------
    func: Callable
        Provide a custom function to execute multiple times with different parameters
    queries: List[dict]
        List of different configurations to be executed
    max_workers: int
        Maximum number of threads to use during execution
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
