Run TCP case study experiments

- Using genie06 (receiver) and genie05 (sender)
- Make sure genie06 is properly configured with DIMMs removed
- Clone genie06 branch of mio on genie06
- Direct attached 100Gbps. port 0 on both. interface should be ens2f0

Setup envirs on both sender and receiver

```
sudo ./setup-envir.sh -i ens2f0 -a 192.168.10.119 -m 9000 -o 1 -d 0 -f 1 -r 0 -p 0
sudo ./setup-envir.sh -i ens2f0 -a 192.168.10.118 -m 9000 -o 1 -d 0 -f 1 -r 0 -p 0
```

Run server on receiver

```
sudo ./run-netapp-tput.sh -m server -o test -S 4 -c 0,4,8,12
```

Run client on sender

```
sudo ./run-netapp-tput.sh -m client -o test -S 4 -C 4 -a 192.168.10.119 -c 0,4,8,12
```

Run mio on receiver (quad 1)

```
sudo python3 -m mio 9kclean-tcp-quad1 --ant_cpus 16,20,24,28 --ant_num_cores 1-4 --ant_mem_numa 0 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120 --disable_prefetch --stats
```

Run mio on receiver (quad 3)

```
sudo python3 -m mio 9kclean-tcp-quad3 --ant_cpus 16,20,24,28 --ant_num_cores 1-4 --ant_mem_numa 0 --ant stream --ant_writefrac 50 --ant_inst_size 64 --ant_duration 120 --disable_prefetch --stats
```
