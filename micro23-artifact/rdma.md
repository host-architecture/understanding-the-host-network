Run RDMA case study experiments

- Using genie06 (server) and genie05 (client)
- Make sure genie06 is properly configured with DIMMs removed
- Clone genie06 branch of mio on genie06
- Direct attached 100Gbps. port 0 on both. interface should be ens2f0

Setup envirs on both sender and receiver

```
sudo ./setup-envir.sh -i ens2f0 -a 192.168.10.119 -m 4096 -d 0 -f 1 -r 1 -p 1
sudo ./setup-envir.sh -i ens2f0 -a 192.168.10.118 -m 4096 -d 0 -f 1 -r 1 -p 1
```

RDMA writes

On server:

```
sudo taskset -c 0 ib_write_bw -d mlx5_0 -x 1 --cpu_util --report_gbits -s 65536 -m 4096 -S 0 -D10000
```

On client:

```
sudo taskset -c 0 ib_write_bw 192.168.10.119 -F -d mlx5_0 -x 1 --cpu_util --report_gbits -s 65536 -m 4096 -S 0 -D10000
```

RDMA reads

On server:

```
sudo taskset -c 0 ib_read_bw -d mlx5_0 -x 1 --cpu_util --report_gbits -s 65536 -m 4096 -S 0 -D10000
```

On client:

```
sudo taskset -c 0 ib_read_bw 192.168.10.119 -F -d mlx5_0 -x 1 --cpu_util --report_gbits -s 65536 -m 4096 -S 0 -D10000
```

Run mio on server (quad 1):

```
sudo python3 -m mio rdma-quad1 --ant_cpus 8,12,16,20,24,28 --ant_num_cores 1-6 --ant_mem_numa 0 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120 --disable_prefetch --stats
```

Run mio on server (quad 2):

```
sudo python3 -m mio rdma-quad2 --ant_cpus 8,12,16,20,24,28 --ant_num_cores 1-6 --ant_mem_numa 0 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120 --disable_prefetch --stats
```

Run mio on server (quad 3):

```
sudo python3 -m mio rdma-quad3 --ant_cpus 8,12,16,20,24,28 --ant_num_cores 6 --ant_mem_numa 0 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 10000 --disable_prefetch
```


Run mio on server (quad 4):

```
sudo python3 -m mio rdma-quad4 --ant_cpus 8,12,16,20,24,28 --ant_num_cores 1-6 --ant_mem_numa 0 --ant stream --ant_writefrac 50 --ant_inst_size 64 --ant_duration 120 --disable_prefetch --stats
```