import sys, argparse, json
from datetime import datetime as dt

sys.path.insert(0, "../python")
from network import *
from protocols import *
from adversary import *
from simulator import *
from data import GoerliTestnet
from experiments import run_and_eval, run_experiment


def run_single_experiment(config):
    nw_generator = NodeWeightGenerator(config["nw_gen_mode"])
    ew_generator = EdgeWeightGenerator(config["ew_gen_mode"])
    if config["network_size"] == 0:
        G = GoerliTestnet().graph
        net = Network(nw_generator, ew_generator, graph=G)
        num_msg = int(G.number_of_nodes() * config["msg_fraction"])
    else:
        net = Network(
            nw_generator, ew_generator, config["network_size"], config["degree"]
        )
        num_msg = int(config["network_size"] * config["msg_fraction"])
    protocols = [BroadcastProtocol(net, broadcast_mode=config["broadcast_mode"])]
    for broadcast_proba in config["dandelion_broadcast_probas"]:
        protocols.append(
            DandelionProtocol(
                net, broadcast_proba, broadcast_mode=config["broadcast_mode"]
            )
        )
        protocols.append(
            DandelionPlusPlusProtocol(
                net, broadcast_proba, broadcast_mode=config["broadcast_mode"]
            )
        )
    single_run_results = []
    for protocol in protocols:
        adv = Adversary(
            protocol, ratio=config["adversary_ratio"], active=config["active_adversary"]
        )
        new_reports = run_and_eval(adv, num_msg)
        single_run_results += new_reports
    # print(config["adversary_ratio"])
    return single_run_results


parser = argparse.ArgumentParser(
    description="Script for experimenting with baseline protocols (Broadcast, Dandelion, Dandelion++)"
)
parser.add_argument(
    "--network_size",
    type=int,
    default=500,
    help="P2P network size (Default: 0). If you specify 0 then Goerli Testnet is used.",
)
parser.add_argument(
    "--degree",
    type=int,
    default=50,
    help="P2P network degree in the random regular graph model (Default: 50)",
)
parser.add_argument(
    "--ew_gen_mode",
    type=str,
    choices=["random", "normal"],
    default="normal",
    help="EdgeWeightGenerator mode (Default: normal)",
)
parser.add_argument(
    "--nw_gen_mode",
    type=str,
    choices=["random", "stake"],
    default="random",
    help="NodeWeightGenerator mode (Default: random)",
)
parser.add_argument(
    "--msg_fraction",
    type=float,
    default=0.05,
    help="Fraction of nodes that send message in one simulation (Default: 0.05)",
)
parser.add_argument(
    "--broadcast_mode",
    type=str,
    choices=["sqrt", "all"],
    default="sqrt",
    help="Define whether a node sends message to all neighbors or just a square root amount of them (Default: sqrt)",
)
parser.add_argument(
    "--dandelion_broadcast_probas",
    nargs="+",
    type=float,
    default=[],
    help="Broadcast probabilities for Dandelion(++) (Default: [] - Dandelion is not executed)",
)
parser.add_argument(
    "--adversary_ratios",
    nargs="+",
    type=float,
    default=[0.1],
    help="Adversary ratios for the experiment (Default: [0.1])",
)
parser.add_argument(
    "--active_adversary",
    action="store_true",
    help="Set to use active adversary in the experiment",
)
parser.add_argument(
    "--num_trials", type=int, default=1, help="Number of trials (Default: 1)"
)
parser.add_argument(
    "--max_threads",
    type=int,
    default=1,
    help="Maximum number of threads used to parallelize the execution (Default: 1)",
)
parser.add_argument(
    "--output_file_prefix",
    type=str,
    default=None,
    help="Specify output file prefix. Otherwise the timestamp will be used.",
)

if __name__ == "__main__":
    # load arguments
    args = parser.parse_args()
    adversary_ratios = args.adversary_ratios
    num_trials = args.num_trials
    max_threads = args.max_threads
    if args.output_file_prefix != None:
        output_file_prefix = args.output_file_prefix
    else:
        output_file_prefix = dt.now().strftime("%Y-%m-%d_%H:%M:%S")

    # save config file
    config = vars(args)
    with open("%s.json" % output_file_prefix, "w") as f:
        f.write(json.dumps(config))

    # prepare queries
    queries = []
    for adv_ratio in adversary_ratios * num_trials:
        query = config.copy()
        query["adversary_ratio"] = adv_ratio
        queries.append(query)
        # print(query)
    print(len(queries))

    # run experiment
    results_df = run_experiment(run_single_experiment, queries, max_threads)
    # save results
    results_df.to_csv("%s.csv" % output_file_prefix, index=False)
