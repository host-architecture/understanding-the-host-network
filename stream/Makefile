CC = gcc
CFLAGS = -O3 -msse4 -mavx512f -g -march=native -funroll-loops

FC = gfortran
FFLAGS = -O2 -fopenmp

all: stream

stream:
	#$(CC) $(CFLAGS) -DNTIMES=1000 -DSTREAM_ARRAY_SIZE=2097152 stream.c -o stream
	$(CC) $(CFLAGS) -DNTIMES=1000 -DSTREAM_ARRAY_SIZE=134217728 stream.c -o stream

stream_f.exe: stream.f mysecond.o
	$(CC) $(CFLAGS) -c mysecond.c
	$(FC) $(FFLAGS) -c stream.f
	$(FC) $(FFLAGS) stream.o mysecond.o -o stream_f.exe

stream_c.exe: stream.c
	$(CC) $(CFLAGS) stream.c -o stream_c.exe

clean:
	rm -f stream stream_f.exe stream_c.exe *.o

# an example of a more complex build line for the Intel icc compiler
stream.icc: stream.c
	icc -O3 -xCORE-AVX2 -ffreestanding -qopenmp -DSTREAM_ARRAY_SIZE=80000000 -DNTIMES=20 stream.c -o stream.omp.AVX2.80M.20x.icc
