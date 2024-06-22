#!/bin/bash

isoconfig="aug23-redis"
colconfig="aug23-redis-p2mwrite"
colconfig_ddio="aug23-redis-p2mwrite-ddio"

# Redis
# Slowdown
rm ~/uhmc-nsdi24/results/oldserver/redis/ddiooff-slowdown.tsv
for i in 1 2 3; do
	iso_xput=$(python3 ../collect_stats.py $isoconfig-cores$i core:redis_xput:sum --filter_num_cores $i);
	col_xput=$(python3 ../collect_stats.py $colconfig-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	col_io_xput=$(python3 ../collect_stats.py $colconfig-cores$i io:io_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	paste <(echo $i) <(awk -v iso=$iso_xput -v col=$col_xput 'BEGIN {print iso/col;}') <(awk -v col=$col_io_xput 'BEGIN {print 13.85/col;}') >> ~/uhmc-nsdi24/results/oldserver/redis/ddiooff-slowdown.tsv
done;

rm ~/uhmc-nsdi24/results/oldserver/redis/slowdown.tsv
for i in 1 2 3; do
	iso_xput=$(python3 ../collect_stats.py $isoconfig-cores$i core:redis_xput:sum --filter_num_cores $i);
	col_xput=$(python3 ../collect_stats.py $colconfig_ddio-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	col_io_xput=$(python3 ../collect_stats.py $colconfig_ddio-cores$i io:io_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	paste <(echo $i) <(awk -v iso=$iso_xput -v col=$col_xput 'BEGIN {print iso/col;}') <(awk -v col=$col_io_xput 'BEGIN {print 13.85/col;}') >> ~/uhmc-nsdi24/results/oldserver/redis/slowdown.tsv
done;

#MemBW
for i in 1 2 3; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:memreadbw:sum,imc:memwritebw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1-600)/1e3, $2/1e3}'); done > ~/uhmc-nsdi24/results/oldserver/redis/ddiooff-membw.tsv
for i in 1 2 3; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig_ddio-cores$i imc:memreadbw:sum,imc:memwritebw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1-600)/1e3, $2/1e3}'); done > ~/uhmc-nsdi24/results/oldserver/redis/membw.tsv

