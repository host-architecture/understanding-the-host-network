## STREAM*

This is a modified version of the standard STREAM benchmark which supports different read/write ratios and memory access patterns.

### Requirements

The benchmark code currently uses AVX-512 to generate 64 byte load/store instructions, and therefore requires a processor with AVX-512 support. You can check whether your processor provides the necessary support using the following:
```
cat /proc/cpuinfo | grep avx512f
```

We have tested STREAM* on the following platforms:
* Ubuntu 20.04, gcc version 8.4.0, Intel Cascade Lake architecture
* Ubuntu 22.04, gcc version 11.4.0, Intel Ice Lake architecture

### Compiling

To compile, simply run
```
make
```

### Usage

To run the benchmark:
```
./stream <workload> <duration>
```

For example, to run 64-byte sequential read workload for 10 seconds:
```
./stream Read64 10
```