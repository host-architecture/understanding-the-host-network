Run redis

```
for i in 1 2 3; do sudo python3 -m mio aug23-redis-p2mwrite --ant_num_cores $((2*i)) --ant_mem_numa 3 --ant redis --ant_duration 1000 --fio --fio_mem_numa 3 --fio_cpus 3,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 4 --fio_duration 1000 --fio_until_ant --disable_prefetch --stats_membw; done;
```

Run GAPBS

```
for i in 1 2 3 4 5 6; do sudo python3 -m mio aug23-gapbs-p2mwrite-ddio --ant_num_cores $i --ant_mem_numa 3 --ant gapbs --ant_duration 1000 --fio --fio_mem_numa 3 --fio_cpus 3,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 4 --fio_duration 1000 --fio_until_ant --disable_prefetch --stats_membw; done;
```