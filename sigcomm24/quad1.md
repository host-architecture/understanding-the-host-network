Run Quadrant 1 experiments

Isolated
```
sudo python3 -m mio artifact-c2m-read --ant_num_cores 1-6 --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120 --disable_prefetch --stats
```

Colocated
```
sudo python3 -m mio artifact-quad1 --ant_num_cores 1-6 --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120 --fio --fio_mem_numa 3 --fio_cpus 3,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 6 --sync_durations --disable_prefetch --stats
```

Bank distribution
```
sudo python3 -m mio artifact-bconf-quad1 --ant_num_cores 1 --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120 --fio --fio_mem_numa 3 --fio_cpus 3,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 4 --sync_durations --disable_prefetch
```
 In parallel run
 ```
 sudo taskset -c 31 ./poll_banks
 cat log.bconf | awk 'NR > 1 {b1 += $4; b2 += $5; b3 += $6; b4 += $7; if(b1+b2+b3+b4 >= 1000 && cnt <= 10000) { cnt += 1; bmax=0; if(b1 > bmax) {bmax = b1;} if(b2 > bmax) {bmax = b2;} if(b3 > bmax) {bmax=b3;} if(b4 > bmax) {bmax = b4;} bavg=(b1+b2+b3+b4)/4; if(bavg > 0) {print bmax/bavg;} b1=0;b2=0;b3=0;b4=0; }}' | sort -n | awk '{print $1, NR}' > ~/membw-eval/artifact-bconf-quad1-cores1.bankcdf.txt
 ```

Figure 7a (Latency + formula)
```
for i in 1 2 3 4 5 6; do paste <(echo $i) <(python3 collect_stats.py artifact-c2m-read-cores$i core:l1_miss_latency:avg --filter_num_cores $i) <(python3 collect_stats.py artifact-quad1-cores$i core:l1_miss_latency:avg,model:readlatcpu:latency --filter_num_cores $i --filter_core_list 11,15,19,23,27,31 ); done
```
