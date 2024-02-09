#!/bin/bash

outpath=$1 #~/uhmc-sigcomm24
isoconfig=$2 #"aug23-redis"
colconfig=$3 #"redis-p2mread"
label=$4 #"redis-p2mread"
p2mrw=$5

iso_corelist="1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61,63"
col_corelist="9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61,63"
ssd_list="SSD0,SSD1,SSD2,SSD3,SSD4,SSD5,SSD6,SSD7"
channel_list="SKT1CHAN0,SKT1CHAN2,SKT1CHAN4,SKT1CHAN6"

if [[ "$p2mrw" == "p2mwrite" ]]; then
	io_iso_xput=26;  
else
	io_iso_xput=16.27;
fi

mkdir -p $outpath/results/newserver/$label;

# Redis
# Slowdown
rm $outpath/results/newserver/$label/slowdown.tsv
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do
	echo $i;
	iso_xput=$(python3 ../collect_stats.py $isoconfig-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list $iso_corelist);
	col_xput=$(python3 ../collect_stats.py $colconfig-cores$i core:redis_xput:sum --filter_num_cores $i --filter_core_list $col_corelist);
	col_io_xput=$(python3 ../collect_stats.py $colconfig-cores$i io:io_xput:sum --filter_num_cores $i --filter_core_list $col_corelist --filter_ssds $ssd_list);
	paste <(echo $i) <(awk -v iso=$iso_xput -v col=$col_xput 'BEGIN {print iso/col;}') <(awk -v col=$col_io_xput -v iso=$io_iso_xput 'BEGIN {print iso/col;}') >> $outpath/results/newserver/$label/slowdown.tsv
done;

#MemBW
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do paste <(echo $i) <(python3 ../collect_stats.py $colconfig-cores$i imc:memreadbw:sum,imc:memwritebw:sum,io:io_xput:sum --filter_num_cores $i --filter_core_list $col_corelist --filter_channels $channel_list --filter_ssds $ssd_list | awk -v io=$io_iso_xput '{print ($1+$2)/1e3-$3, $3}'); done > $outpath/results/newserver/$label/membw.tsv

