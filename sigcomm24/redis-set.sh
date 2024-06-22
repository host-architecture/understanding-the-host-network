#!/bin/bash

isoconfig="redis-set-iso"
colconfig="redis-set-p2mwrite"
colconfig_ddio="redis-set-p2mwrite-ddio"

# Redis
# Slowdown
rm ~/uhmc-sigcomm24/results/oldserver/redis-set/ddiooff-slowdown.tsv
for i in 1 2 3; do
	iso_xput=$(python3 ../collect_stats.py $isoconfig-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list 3,7,11,15,19,23,27,31);
	col_xput=$(python3 ../collect_stats.py $colconfig-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	col_io_xput=$(python3 ../collect_stats.py $colconfig-cores$i io:io_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	paste <(echo $i) <(awk -v iso=$iso_xput -v col=$col_xput 'BEGIN {print iso/col;}') <(awk -v col=$col_io_xput 'BEGIN {print 13.85/col;}') >> ~/uhmc-sigcomm24/results/oldserver/redis-set/ddiooff-slowdown.tsv
done;

rm ~/uhmc-sigcomm24/results/oldserver/redis-set/slowdown.tsv
for i in 1 2 3; do
	iso_xput=$(python3 ../collect_stats.py $isoconfig-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list 3,7,11,15,19,23,27,31);
	col_xput=$(python3 ../collect_stats.py $colconfig_ddio-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	col_io_xput=$(python3 ../collect_stats.py $colconfig_ddio-cores$i io:io_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	paste <(echo $i) <(awk -v iso=$iso_xput -v col=$col_xput 'BEGIN {print iso/col;}') <(awk -v col=$col_io_xput 'BEGIN {print 13.85/col;}') >> ~/uhmc-sigcomm24/results/oldserver/redis-set/slowdown.tsv
done;

#MemBW
for i in 1 2 3; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:memreadbw:sum,imc:memwritebw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1+$2)/1e3-13.86, 13.86}'); done > ~/uhmc-sigcomm24/results/oldserver/redis-set/ddiooff-membw.tsv
for i in 1 2 3; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig_ddio-cores$i imc:memreadbw:sum,imc:memwritebw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1+$2)/1e3-13.86, 13.86}'); done > ~/uhmc-sigcomm24/results/oldserver/redis-set/membw.tsv

