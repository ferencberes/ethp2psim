import argparse, json
from datetime import datetime as dt

from ethp2psim.network import *
from ethp2psim.protocols import *
from ethp2psim.adversary import *
from ethp2psim.simulator import *
from ethp2psim.data import GoerliTestnet
from ethp2psim.experiments import run_and_eval, run_experiment


def get_adversary_for_protocol(
    protocol: Protocol, is_active: bool, nodes: list, seed: int = None
) -> Adversary:
    """
    Generate adversary with respect to the given parameters

    Parameters
    ----------
    protocol : protocol
        The protocol that you intend to break with an adversary
    is_active : bool
        Set whether the adversary is allowed to refuse to propagate any message
    nodes : list
        List of adversarial node IDs
    seed : int
        Random seed for the experiment

    """
    if isinstance(protocol, DandelionProtocol):
        adv = DandelionAdversary(
            protocol,
            active=is_active,
            adversaries=nodes,
            seed=seed,
        )
    elif isinstance(protocol, OnionRoutingProtocol):
        adv = OnionRoutingAdversary(
            protocol,
            active=is_active,
            adversaries=nodes,
            seed=seed,
        )
    else:
        adv = Adversary(
            protocol,
            active=is_active,
            adversaries=nodes,
            seed=seed,
        )
    return adv


def run_single_experiment(config: dict) -> list:
    seed = np.random.randint(10**5)
    nw_generator = NodeWeightGenerator(config["nw_gen_mode"])
    ew_generator = EdgeWeightGenerator(config["ew_gen_mode"])
    if config["network_size"] == 0:
        G = GoerliTestnet().graph
        net = Network(nw_generator, ew_generator, graph=G, seed=seed)
        num_msg = int(G.number_of_nodes() * config["msg_fraction"])
    else:
        net = Network(
            nw_generator,
            ew_generator,
            config["network_size"],
            config["degree"],
            seed=seed,
        )
        num_msg = int(config["network_size"] * config["msg_fraction"])
    protocols = []
    # decide whether to execute the simple BroadcastProtocol
    if not config["exclude_simple_broadcast"]:
        protocols.append(
            BroadcastProtocol(net, broadcast_mode=config["broadcast_mode"], seed=seed)
        )
    # add Dandelion(++) instances to the experiment if the related parameters were defined
    for spreading_proba in config["dandelion_spreading_probas"]:
        protocols.append(
            DandelionProtocol(
                net, spreading_proba, broadcast_mode=config["broadcast_mode"], seed=seed
            )
        )
        protocols.append(
            DandelionPlusPlusProtocol(
                net, spreading_proba, broadcast_mode=config["broadcast_mode"], seed=seed
            )
        )
    # add OnionRoutingProtocol instances to the experiment if the related parameters were defined
    for num_relayers in config["onion_routing_num_relayers"]:
        protocols.append(
            OnionRoutingProtocol(
                net, num_relayers, broadcast_mode=config["broadcast_mode"], seed=seed
            )
        )
    # use the same set of adversarial nodes for all protocols
    num_adv_nodes = int(net.num_nodes * config["adversary_ratio"])
    if config["adversary_centrality_metric"] != "none":
        adv_nodes = net.get_central_nodes(
            num_adv_nodes, config["adversary_centrality_metric"]
        )
    else:
        adv_nodes = net.sample_random_nodes(num_adv_nodes, False)
    single_run_results = []
    for protocol in protocols:
        # generate adversary with respect to the protocol
        adv = get_adversary_for_protocol(
            protocol, config["active_adversary"], adv_nodes, seed
        )
        # by fixing the seed we sample the same messages
        sim = Simulator(adv, num_msg, seed=seed, verbose=False)
        # print()
        # print(sim.messages)
        new_reports = run_and_eval(sim)
        single_run_results += new_reports
    return single_run_results


parser = argparse.ArgumentParser(
    description="Script for experimenting with baseline protocols (Broadcast, Dandelion, Dandelion++)"
)
parser.add_argument(
    "--network_size",
    type=int,
    default=500,
    help="P2P network size (Default: 500). If you specify 0 then Goerli Testnet is used.",
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
    default=0.1,
    help="Fraction of nodes that send message in one simulation (Default: 0.1)",
)
parser.add_argument(
    "--broadcast_mode",
    type=str,
    choices=["sqrt", "all"],
    default="sqrt",
    help="Define whether a node sends message to all neighbors or just a square root amount of them (Default: sqrt)",
)

parser.add_argument(
    "--exclude_simple_broadcast",
    action="store_true",
    help="Exclude the simple BroadcastProtocol from the experiments. By default it is always executed.",
)

parser.add_argument(
    "--dandelion_spreading_probas",
    nargs="+",
    type=float,
    default=[],
    help="Broadcast probabilities for Dandelion(++) (Default: [] - Dandelion is not executed)",
)

parser.add_argument(
    "--onion_routing_num_relayers",
    nargs="+",
    type=int,
    default=[],
    help="Number of relayers in OnionRoutingProtocol (Default: [] - OnionRoutingProtocol is not executed)",
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
    "--adversary_centrality_metric",
    type=str,
    choices=["degree", "betweenness", "pagerank", "none"],
    default="none",
    help="Set metric to choose top central nodes to be adversaries.",
)
parser.add_argument(
    "--num_trials", type=int, default=1, help="Number of trials (Default: 1)"
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
    max_threads = 1
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
