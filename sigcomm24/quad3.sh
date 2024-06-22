#!/bin/bash

isoconfig="march23-quad3-iso-cpu"
colconfig="aug23-quad3"
colconfig_bconf="aug23-bconf-quad3"

#Fig 9a
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i core:l1_miss_latency:avg,model:readlatcpu:latency,cha:drd_latency:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 --filter_irps SKT3IRP1 | awk '{print $1, $2 + $1 - $3+10}' ); done > ~/uhmc-nsdi24/results/oldserver/quad3/model-latency.tsv

# Fig 9b
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31); done > ~/uhmc-nsdi24/results/oldserver/quad3/rpq-occupancy.tsv

#Fig 9c
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i | awk '{print ($1+$2)/($3*1e6/64)}') <(python3 ../collect_stats.py $colconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1+$2)/($3*1e6/64)}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad3/rowmiss.tsv

#Fig 7d
# TODO bankcdf
#cp ~/uhmc-stats/membw-eval/$colconfig_bconf-cores1.bankcdf.txt ~/uhmc-nsdi24/results/oldserver/bconf/nreq-quad3-cores1.bankcdf.txt

#Fig 9d
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i model:readlatcpu:switching,model:readlatcpu:writehol,model:readlatcpu:rowmiss,model:readlatcpu:remainder,core:l1_miss_latency:avg,cha:drd_latency:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print $1, $2, $3, $4, $5-$6}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad3/model-breakdown.tsv

#Fig 9e
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none,io:io_xput:sum,model:writelatio47:latency,cha:blemon_latency:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 --filter_irps SKT3IRP1 --filter_ssds SSD0,SSD1,SSD2,SSD3 | awk '{print $1/($2/64), $3 + $1/($2/64) - $4 - 205}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad3/wrmodel-latency.tsv

#Fig 9f
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:pfillwpq34:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print $1}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad3/pfillwpq.tsv

#fIG 9g
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 --filter_irps SKT3IRP1) ; done > ~/uhmc-nsdi24/results/oldserver/quad3/iioocc.tsv

#Fig 9h
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i model:writelatio47:switching,model:writelatio47:readhol,model:readlatcpu:rowmiss,model:readlatcpu:writehol,irp:irp_occupancy:none,io:io_xput:sum,cha:blemon_latency:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 --filter_irps SKT3IRP1 --filter_ssds SSD0,SSD1,SSD2,SSD3 | awk '{print $1, $2, $3, $4, $5/($6/64) - $7 - 205}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad3/wrmodel-breakdown.tsv

