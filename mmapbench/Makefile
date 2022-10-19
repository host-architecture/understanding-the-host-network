CC = gcc
CFLAGS = -O3 -msse4 -g -march=native -funroll-loops

all: mmapbench

mmapbench:
	$(CC) $(CFLAGS) mmapbench.c -o mmapbench

clean:
	rm -f mmapbench *.o

