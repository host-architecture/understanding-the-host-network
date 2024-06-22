## Overview
`mio` is a unified framework for experimenting with and understanding the host network on real server hardware (The name is inspired by `fio` a popular storage benchmarking tool, although `mio` is not really a benchmarking tool in itself). `mio` provides the following functionality:

* **Colocating multiple applications**: `mio` makes it easy to simultaneously run multiple applications/workloads in order to emulate colocated/multitenant deployments which are common in datacenters. It provides convenient wrappers for several applications and standard benchmark tools making it possible to run them with configurable parameters using a single common command line interface.
* **Measuring and collecting statistics**: During application runs, `mio` has extensive support for capturing useful statistics including higher-level metrics (e.g., CPU utilization, Memory bandwidth utilization, cache miss rates) and lower-level metrics (e.g, memory access latency, memory controller queue occupancy). It supports both low-overhead coarse-grained measurements (millisecond scale), and finer-grained (sub-microsecond scale) measurements using a dedicated busy polling CPU core. It also provides a flexible way to collect, aggregate, and query the measured statistics through a single command line interface.
* **Deeper analysis**: `mio` additionally provides tools for deeper analysis of the measured low-level metrics. In particular, it can connect level measurements to the observed end-to-end memory access latency using an analytical formula. (this feature is currently supported on Intel Cascade Lake platforms).

## Applications
`mio` supports two kinds of applications: (1) Applications on CPU cores, which generate CPU core to memory traffic (which we call C2M applications) and (2) Applications which generate Peripheral to memory traffic (which we call P2M applications) through DMAs from Peripheral devices such as SSDs, NICs and GPUs. `mio` currently supports the following applications:

C2M Applications:
* Redis: A popular in-memory key-value store.
* GAPBS: A popular graph processing benchmark.
* STREAM*: An extended version of the standard STREAM memory bandwidth benchmark with support for different read/write ratios and access patterns.
* MLC: Intel's Memory Latency Checker (MLC) benchmarking tool.

P2M Applications:
* fio: Standard storage benchmarking tool.
* mmapbench: Custom benchmark tool that uses the mmap interface to perform storage I/O.

Extending `mio` to support other applications is easy --- one simply needs write a wrapper that implements the `MemoryAntagonist` interface.

## Usage

Make sure to configure `config.json` correctly based on your setup

Running C2M Application (STREAM*) in isolation:
```
sudo python3 -m mio c2m-iso --ant_num_cores 1 --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120
```

Running P2M Application (fio) in isolation:
```
sudo python3 -m mio p2m-iso --fio --fio_mem_numa 3 --fio_cpus 3,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 4 --fio_duration 120
```

Colocate C2M and P2M application:
```
sudo python3 -m mio c2m-p2m --ant_num_cores 1 --ant_mem_numa 3 --ant stream --ant_writefrac 0 --ant_inst_size 64 --ant_duration 120 --fio --fio_mem_numa 3 --fio_cpus 3,7 --fio_writefrac 0 --fio_iosize $((8*1024*1024)) --fio_iodepth 64 --fio_num_ssds 4 --sync_durations --stats
```

Collect/query statistics from the above run (average LFB latency and average RPQ occupancy in this example):
```
python3 collect_stats.py c2m-p2m-cores1 core:l1_miss_latency:avg,imc:rpq_occupancy:avg
```