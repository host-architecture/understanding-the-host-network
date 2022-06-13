#!/bin/bash

config=$1
io_size=$2
STATS_PATH=/home/midhul/membw-eval

cat $STATS_PATH/$config.fio*.txt  | grep "iops        :" | awk '{print$5}' | tr -d 'avg=' | tr -d ',' | awk -v sz=$io_size '{s += $1} END {print s*sz*8/1e9;}'