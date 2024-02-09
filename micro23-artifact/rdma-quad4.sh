#!/bin/bash

isoconfig="aug23-c2m-read"
colconfig="rdma-quad4"
# colconfig_bconf="aug23-bconf-quad4"

#Fig 8a
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i core:l1_miss_latency:avg,model:readlatcpuadj:latency --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 ); done > ~/uhmc-sigcomm24/results/oldserver/rdma/quad4/model-latency.tsv

# Fig 8b
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_channels SKT3CHAN0,SKT3CHAN3) <(python3 ../collect_stats.py $colconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_core_list 8,12,16,20,24,28); done > ~/uhmc-sigcomm24/results/oldserver/rdma/quad4/rpq-occupancy.tsv

#Fig 7c
#for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i | awk '{print ($1+$2)/($3*1e6/64)}') <(python3 ../collect_stats.py $colconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 | awk '{print ($1+$2)/($3*1e6/64)}') ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad4/rowmiss.tsv

#Fig 7d
# TODO bankcdf
#cp ~/uhmc-stats/membw-eval/$colconfig_bconf-cores1.bankcdf.txt ~/uhmc-sigcomm24/results/oldserver/bconf/nreq-quad4-cores1.bankcdf.txt

#Fig 8c
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i model:readlatcpuadj:switching,model:readlatcpuadj:writehol,model:readlatcpuadj:rowmiss,model:readlatcpuadj:remainder --filter_num_cores $i --filter_core_list 8,12,16,20,24,28) ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad4/model-breakdown.tsv

#Fig 8d
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i cha:rdcur_occupancy:sum --filter_num_cores $i --filter_core_list 8,12,16,20,24,28) ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad4/rdcurocc.tsv

#Fig 7g
#for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:pfillwpq34:none --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 | awk '{print $1}') ; done  > ~/uhmc-sigcomm24/results/oldserver/rdma/quad4/pfillwpq.tsv

#fIG 7h
#for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none --filter_num_cores $i --filter_core_list 8,12,16,20,24,28 --filter_irps SKT3IRP1) ; done > ~/uhmc-sigcomm24/results/oldserver/rdma/quad4/iioocc.tsv

