import sys

sys.path.insert(0, "../python")
from network import *
from protocols import *
from adversary import *
from simulator import *
from experiments import run_and_eval, run_experiment


def run_single_experiment(config):
    nw_generator = NodeWeightGenerator("random")
    ew_generator = EdgeWeightGenerator("normal")
    net = Network(nw_generator, ew_generator, config["network_size"], config["degree"])
    adv = Adversary(net, config["adv_ratio"], config["is_active_adversary"])
    protocols = [BroadcastProtocol(net, broadcast_mode=config["bc_mode"])]
    for broadcast_proba in config["dandelion_bc_probas"]:
        protocols.append(
            DandelionProtocol(net, broadcast_proba, broadcast_mode=config["bc_mode"])
        )
        protocols.append(
            DandelionPlusPlusProtocol(
                net, broadcast_proba, broadcast_mode=config["bc_mode"]
            )
        )
    single_run_results = []
    for protocol in protocols:
        new_reports = run_and_eval(net, adv, protocol, config["num_msg"])
        single_run_results += new_reports
    print(config["adv_ratio"])
    return single_run_results


network_size = 1000
config = {
    "network_size": network_size,
    "num_msg": int(network_size * 0.05),
    "degree": 50,
    "bc_mode": "sqrt",
    "dandelion_bc_probas": [0.5],  # , 0.25, 0.1]
}
adversary_ratios = [0.01, 0.05]  # ,0.1,0.2]
num_trials = 2
max_threads = 4

print(config)

queries = []
for adv_ratio in adversary_ratios * num_trials:
    query = config.copy()
    query["adv_ratio"] = adv_ratio
    query["is_active_adversary"] = False
    queries.append(query)

results_df = run_experiment(run_single_experiment, queries, max_threads)

results_df.to_csv("compare_baselines_results.csv", index=False)
