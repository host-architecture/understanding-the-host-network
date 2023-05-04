# mio
`mio` is a unified framework for experimenting with and understanding main memory contention between different applications/workloads on real server hardware (The name is inspired by `fio` a popular storage benchmarking tool, although `mio` is not really a benchmarking tool in itself). `mio` provides the following functionality:

* **Colocating multiple applications**: `mio` makes it easy to simultaneously run multiple applications/workloads in order to emulate colocated/multitenant deployments which are common in datacenters. It provides convenient wrappers for several applications and standard benchmark tools making it possible to run them with configurable parameters using a single common command line interface.
* **Measuring and collecting statistics**: During application runs, `mio` has extensive support for capturing useful statistics including higher-level metrics (e.g., CPU utilization, Memory bandwidth utilization, cache miss rates) and lower-level metrics (e.g, memory access latency, memory controller queue occupancy). It supports both low-overhead coarse-grained measurements (millisecond scale), and finer-grained (sub-microsecond scale) measurements using a dedicated busy polling CPU core. It also provides a flexible way to collect, aggregate, and query the measured statistics through a single command line interface.
* **Deeper analysis**: `mio` additionally provides tools for deeper analysis of the measured low-level metrics. In particular, it can connect memory controller level measurements to the observed end-to-end memory access latency inflation which is very useful for explaining the impact of main memory contention on application performance (this feature is currently supported on Intel Casacade Lake platforms).  
