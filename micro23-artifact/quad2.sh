#!/bin/bash

isoconfig="aug23-c2m-read"
colconfig="aug23-quad2"
colconfig_bconf="aug23-bconf-quad2"

#Fig 8a
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i core:l1_miss_latency:avg,model:readlatcpu:latency --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 ); done > ~/uhmc-nsdi24/results/oldserver/quad2/model-latency.tsv

# Fig 8b
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31); done > ~/uhmc-nsdi24/results/oldserver/quad2/rpq-occupancy.tsv

#Fig 7c
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i | awk '{print ($1+$2)/($3*1e6/64)}') <(python3 ../collect_stats.py $colconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1+$2)/($3*1e6/64)}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad2/rowmiss.tsv

#Fig 7d
# TODO bankcdf
#cp ~/uhmc-stats/membw-eval/$colconfig_bconf-cores1.bankcdf.txt ~/uhmc-nsdi24/results/oldserver/bconf/nreq-quad2-cores1.bankcdf.txt

#Fig 8c
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i model:readlatcpu:switching,model:readlatcpu:writehol,model:readlatcpu:rowmiss,model:readlatcpu:remainder --filter_num_cores $i --filter_core_list 11,15,19,23,27,31) ; done  > ~/uhmc-nsdi24/results/oldserver/quad2/model-breakdown.tsv

#Fig 8d
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i cha:rdcur_occupancy:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31) ; done  > ~/uhmc-nsdi24/results/oldserver/quad2/rdcurocc.tsv

#Fig 7g
#for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:pfillwpq34:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print $1}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad2/pfillwpq.tsv

#fIG 7h
#for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 --filter_irps SKT3IRP1) ; done > ~/uhmc-nsdi24/results/oldserver/quad2/iioocc.tsv

