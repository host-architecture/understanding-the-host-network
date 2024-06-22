#!/bin/bash

outpath=$1
isoconfig=$2
colconfig=$3
colconfig_ddio=$4
label=$5

mkdir -p $outpath/results/oldserver/$label

# gapbs
# Slowdown
rm $outpath/results/oldserver/$label/ddiooff-slowdown.tsv
for i in 1 2 3 4 5 6; do
	iso_xput=$(python3 ../collect_stats.py $isoconfig-cores$i core:gapbs_time:none --filter_num_cores $i);
	echo "iso done";
	col_xput=$(python3 ../collect_stats.py $colconfig-cores$i core:gapbs_time:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	echo "col done";
	col_io_xput=$(python3 ../collect_stats.py $colconfig-cores$i io:io_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	paste <(echo $i) <(awk -v iso=$iso_xput -v col=$col_xput 'BEGIN {print col/iso;}') <(awk -v col=$col_io_xput 'BEGIN {print 13.95/col;}') >> $outpath/results/oldserver/$label/ddiooff-slowdown.tsv
done;

echo "ddio";

rm $outpath/results/oldserver/$label/slowdown.tsv
for i in 1 2 3 4 5 6; do
	iso_xput=$(python3 ../collect_stats.py $isoconfig-cores$i core:gapbs_time:none --filter_num_cores $i);
	echo "iso done";
	col_xput=$(python3 ../collect_stats.py $colconfig_ddio-cores$i core:gapbs_time:none --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	echo "col done";
	col_io_xput=$(python3 ../collect_stats.py $colconfig_ddio-cores$i io:io_xput:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31);
	echo "io xput done";
	paste <(echo $i) <(awk -v iso=$iso_xput -v col=$col_xput 'BEGIN {print col/iso;}') <(awk -v col=$col_io_xput 'BEGIN {print 13.95/col;}') >> $outpath/results/oldserver/$label/slowdown.tsv
done;

#MemBW
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:memreadbw:sum,imc:memwritebw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1+$2)/1e3-13.9, 13.9}'); done > $outpath/results/oldserver/$label/ddiooff-membw.tsv
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig_ddio-cores$i imc:memreadbw:sum,imc:memwritebw:sum --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 | awk '{print ($1+$2)/1e3-13.9, 13.9}'); done > $outpath/results/oldserver/$label/membw.tsv

