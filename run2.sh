#!/bin/bash

num_cores=$1
config=statstest-pre

for i in {1..5}; do sudo python3 -m mio $config-write0-dur5-run$i --ant_num_cores $num_cores --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --disable_prefetch --ant_duration 60 --stats_single --stats_single_duration 5; done;
for i in {1..5}; do sudo python3 -m mio $config-write0-dur30-run$i --ant_num_cores $num_cores --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --disable_prefetch --ant_duration 60 --stats_single --stats_single_duration 30; done;
for i in {1..5}; do sudo python3 -m mio $config-write0-dur50-run$i --ant_num_cores $num_cores --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --disable_prefetch --ant_duration 60 --stats_single --stats_single_duration 50; done;
