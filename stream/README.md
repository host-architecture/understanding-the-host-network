## STREAM*

This is a modified version of the standard STREAM benchmark which supports different read/write ratios and memory access patterns.

### Compiling

We have tested STREAM* on the following platforms:
* Ubuntu 20.04, gcc version 8.4.0, Intel Cascade Lake architecture
* Ubuntu 22.04, gcc version 11.4.0, Intel Ice Lake architecture

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