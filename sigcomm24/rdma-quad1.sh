#!/bin/bash

isoconfig="aug23-c2m-read"
colconfig="rdma-quad1"
#colconfig_bconf="aug23-bconf-quad1"

#Fig 7a
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i core:l1_miss_latency:avg,model:readlatcpu:latency --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 ); done > ~/uhmc-sigcomm24/results/oldserver/rdma/quad1/model-latency.tsv

# Fig 7b
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_channels SKT3CHAN0,SKT3CHAN3) <(python3 ../collect_stats.py $colconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_core_list 8,12,16,20,24,28); done > ~/uhmc-sigcomm24/results/oldserver/rdma/quad1/rpq-occupancy.tsv

#Fig 7c
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i --filter_channels SKT3CHAN0,SKT3CHAN3 | awk '{print ($1+$2)/($3*1e6/64)}') <(python3 ../collect_stats.py $colconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 | awk '{print ($1+$2)/($3*1e6/64)}') ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad1/rowmiss.tsv

#Fig 7d
# TODO bankcdf
#cp ~/uhmc-stats/membw-eval/$colconfig_bconf-cores1.bankcdf.txt ~/uhmc-sigcomm24/results/oldserver/bconf/nreq-quad1-cores1.bankcdf.txt

#Fig 7e
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i model:readlatcpu:switching,model:readlatcpu:writehol,model:readlatcpu:rowmiss,model:readlatcpu:remainder --filter_num_cores $i --filter_core_list 8,12,16,20,24,28) ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad1/model-breakdown.tsv

#Fig 7f
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 --filter_irps SKT0IRP2 | awk '{print $1/((97.5/8)*1e9/64)*1e9}') ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad1/iolat.tsv

#Fig 7g
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:pfillwpq34:none --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 | awk '{print $1}') ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad1/pfillwpq.tsv

#fIG 7h
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 --filter_irps SKT0IRP2) ; done > ~/uhmc-sigcomm24/results/oldserver/rdma/quad1/iioocc.tsv

