# Understanding the Host Network

The _host network_ integrates processor, memory, peripheral interconnects to enable data transfer between devices (processors, memory, network interface cards, storage devices, accelerators, etc.) within a host. Several recent studies (from [Google](https://conferences.sigcomm.org/hotnets/2022/papers/hotnets22_sagarwal.pdf), [Alibaba](https://www.usenix.org/system/files/fast23-li-qiang_more.pdf), [ByteDance](https://www.usenix.org/system/files/nsdi23-liu-kefei.pdf)) have shown that contention within the host network can have significant impact on networked applications (throughput degradation, tail latency inflation, and isolation violation). 

Our [SIGCOMM'24 paper](https://www.cs.cornell.edu/~midhul/papers/uhnet.pdf) paper builds an in-depth understanding of the various regimes and root causes of contention within the host network. It (1) shows that the impact of contention within the host network is broader than just the context of networked applications (2) demonstrates that contention within the host network is rooted in the poor interplay between processor, memory, and peripheral interconnects (3) presents a conceptual abstraction to explain contention with the host network and its impact on application performance.

This repository supplements our [SIGCOMM'24 paper](https://www.cs.cornell.edu/~midhul/papers/uhnet.pdf) and provides open-source measurement infrastructure to study the host network, including, but not limited to, code and documentation to reproduce/extend experiments from our paper.

## Technical Report
An extended version of our [SIGCOMM'24 paper](https://www.cs.cornell.edu/~midhul/papers/uhnet.pdf), with additional results, is available here: [tech-report.pdf](tech-report.pdf).

## Overview
This repository is organized as follows:
* [`mio`](mio) A tool to that makes it easy to simultaneously run multiple applications/workloads while performing low-overhead measurements of a plethora of metrics at various host network nodes (Memory Controller, Caching and Home Agent, Integrated I/O controller, etc.) 
* [`microsec`](microsec) Infrastructure to perform host network measurements at microsecond-scale using a dedicated CPU core. 
* [`stream`](stream) A modified version of the standard STREAM benchmark which supports different read/write ratios and memory access patterns.
* [`sigcomm24`](sigcomm24) Documentation and scripts to reproduce the experiments from our SIGCOMM'24 paper.

## Current limitations
Currently, our infrastructure primarily supports the Intel Cascade Lake architecture (with partial support for Intel Ice Lake). Extension to other Intel and AMD architectures is an important future direction. Please do reach out if you are interested in contributing to this. 

## Contact

Midhul Vuppalapati ([midhul@cs.cornell.edu](mailto:midhul@cs.cornell.edu))

## Usage

All the contents of this repository can be freely used for research and education purposes. Kindly cite the following publication if you use our tools or find our work helpful:

```
@inproceedings {understanding-the-host-network,
author = {Vuppalapati, Midhul and Agarwal, Saksham and Schuh, Henry N and Kasikci, Baris and Krishnamurthy, Arvind and Agarwal, Rachit},
title = {Understanding the Host Network},
booktitle = {ACM SIGCOMM},
year = {2024}
}
```
