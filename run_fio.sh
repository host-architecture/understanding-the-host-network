#!/bin/bash

STATS_PATH=/home/midhul/membw-eval
FIO_PATH=/home/midhul/fio

config=$1
workload=$2
io_size=$3
io_depth=$4
duration=$5

pids=()

numactl --membind 3 $FIO_PATH/fio --cpus_allowed=0,4 --filename=/dev/nvme0n1 --name test  --ioengine=libaio  --direct=1  --rw=$workload  --gtod_reduce=0  --cpus_allowed_policy=split  --time_based  --size=1G  --runtime=$duration  --numjobs=2  --bs=$io_size  --iodepth=$io_depth --group_reporting > $STATS_PATH/$config.fio0.txt 2>&1 &
pids+=($!);
numactl --membind 3 $FIO_PATH/fio --cpus_allowed=8,12 --filename=/dev/nvme1n1 --name test  --ioengine=libaio  --direct=1  --rw=$workload  --gtod_reduce=0  --cpus_allowed_policy=split  --time_based  --size=1G  --runtime=$duration  --numjobs=2  --bs=$io_size  --iodepth=$io_depth --group_reporting > $STATS_PATH/$config.fio1.txt 2>&1 &
pids+=($!);
numactl --membind 3 $FIO_PATH/fio --cpus_allowed=16,20 --filename=/dev/nvme4n1 --name test  --ioengine=libaio  --direct=1  --rw=$workload  --gtod_reduce=0  --cpus_allowed_policy=split  --time_based  --size=1G  --runtime=$duration  --numjobs=2  --bs=$io_size  --iodepth=$io_depth --group_reporting > $STATS_PATH/$config.fio2.txt 2>&1 &
pids+=($!);
numactl --membind 3 $FIO_PATH/fio --cpus_allowed=24,32 --filename=/dev/nvme5n1 --name test  --ioengine=libaio  --direct=1  --rw=$workload  --gtod_reduce=0  --cpus_allowed_policy=split  --time_based  --size=1G  --runtime=$duration  --numjobs=2  --bs=$io_size  --iodepth=$io_depth --group_reporting > $STATS_PATH/$config.fio3.txt 2>&1 &
pids+=($!);

wait "${pids[@]}"