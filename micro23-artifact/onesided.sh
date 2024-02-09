#!/bin/bash

isoconfig="aug23-c2m-read"
colconfig="aug23-quad1"
colconfig_bconf="aug23-bconf-quad1"
colconfig2="aug23-quad2"
colconfig2_bconf="aug23-bconf-quad2"


#Fig 7a
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i core:l1_miss_latency:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 ) <(python3 ../collect_stats.py $colconfig2-cores$i core:l1_miss_latency:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 ); done > ~/uhmc-nsdi24/results/oldserver/onesided/c2m-latency.tsv

# Fig 7b
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31); <(python3 ../collect_stats.py $colconfig2-cores$i imc:rpq_occupancy:avg --filter_num_cores $i --filter_core_list 11,15,19,23,27,31); done > ~/uhmc-nsdi24/results/oldserver/onesided/rpq-occupancy.tsv

#Fig 7c
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $isoconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i | awk '{print ($1+$2)/($3*1e6/64)}') <(python3 ../collect_stats.py $colconfig-cores$i imc:acts_read:sum,imc:acts_byp:sum,imc:memreadbw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1+$2)/($3*1e6/64)}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad1/rowmiss.tsv

#Fig 7d
# TODO bankcdf
cp ~/uhmc-stats/membw-eval/$colconfig_bconf-cores1.bankcdf.txt ~/uhmc-nsdi24/results/oldserver/bconf/nreq-quad1-cores1.bankcdf.txt

#Fig 7e
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i model:readlatcpu:switching,model:readlatcpu:writehol,model:readlatcpu:rowmiss,model:readlatcpu:remainder --filter_num_cores $i --filter_core_list 11,15,19,23,27,31) ; done  > ~/uhmc-nsdi24/results/oldserver/quad1/model-breakdown.tsv

#Fig 7f
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none,io:io_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 --filter_irps SKT3IRP1 --filter_ssds SSD0,SSD1,SSD2,SSD3 | awk '{print $1/($2*1e9/64)*1e9}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad1/iolat.tsv

#Fig 7g
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:pfillwpq34:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print $1}') ; done  > ~/uhmc-nsdi24/results/oldserver/quad1/pfillwpq.tsv

#fIG 7h
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i irp:irp_occupancy:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 --filter_irps SKT3IRP1) ; done > ~/uhmc-nsdi24/results/oldserver/quad1/iioocc.tsv

