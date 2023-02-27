#!/bin/bash
num_trials=$1
network_size=$2

if [ $network_size -eq 0 ]
then
graph="goerli"
else
graph="random_regular_"$network_size
fi

if [ -z "$3" ]
then
adversary_cm="none"
else
adversary_cm=$3
fi

prefix="$graph"_"$adversary_cm"

echo $prefix

# experiment with passive adversary
python compare_protocols.py --adversary_ratio 0.01 0.05 0.1 0.2 --network_size $network_size --adversary_centrality_metric $adversary_cm --dandelion_spreading_probas 0.5 0.25 0.125 --onion_routing_num_relayers 3 4 5 --num_trials $num_trials --output_file_prefix "$prefix"_with_dandelions
python compare_protocols.py --adversary_ratio 0.01 0.05 0.1 0.2 --network_size $network_size --adversary_centrality_metric $adversary_cm --dandelion_spreading_probas 0.5 0.25 0.125 --onion_routing_num_relayers 3 4 5 --num_trials $num_trials --broadcast_mode all --output_file_prefix "$prefix"_with_dandelions_bc_all

# experiment with active adversary
python compare_protocols.py --adversary_ratio 0.01 0.05 0.1 0.2 --network_size $network_size --adversary_centrality_metric $adversary_cm --dandelion_spreading_probas 0.5 0.25 0.125 --onion_routing_num_relayers 3 4 5 --num_trials $num_trials --active_adversary --output_file_prefix "$prefix"_with_dandelions_active_adversary
python compare_protocols.py --adversary_ratio 0.01 0.05 0.1 0.2 --network_size $network_size --adversary_centrality_metric $adversary_cm --dandelion_spreading_probas 0.5 0.25 0.125 --onion_routing_num_relayers 3 4 5 --num_trials $num_trials --active_adversary --broadcast_mode all --output_file_prefix "$prefix"_with_dandelions_active_adversary_bc_all