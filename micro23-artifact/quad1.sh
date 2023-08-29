#!/bin/bash

#Fig 7a
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py aug23-quad1-cores$i core:l1_miss_latency:avg,model:readlatcpu:latency --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 ); done > ~/uhmc-osdi23/results/oldserver/quad1/model-latency.tsv