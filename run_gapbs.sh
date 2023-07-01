for i in 1 4 8 12 16 20 24 28; do python3 -m mio gapbs-iso-noprefetch --ant gapbs --ant_num_cores $i --ant_duration 100 --disable_prefetch --stats; done

for i in 1 4 8 12 16 20 24 28; do python3 -m mio gapbs-combined-noprefetch --ant gapbs --ant_num_cores $i --ant_duration 100 --fio --fio_mem_numa 1 --fio_cpus 1,3,5,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 8 --fio_until_ant --disable_prefetch --stats; done

for i in 1 4 8 12 16 20 24 28; do python3 -m mio gapbs-iso-prefetch --ant gapbs --ant_num_cores $i --ant_duration 100 --stats; done

for i in 1 4 8 12 16 20 24 28; do python3 -m mio gapbs-combined-prefetch --ant gapbs --ant_num_cores $i --ant_duration 100 --fio --fio_mem_numa 1 --fio_cpus 1,3,5,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 8 --fio_until_ant --stats; done
