CC = gcc
CFLAGS = -O0 -msse4 -g -march=native -funroll-loops

all: gups

gups:
	$(CC) $(CFLAGS) gups.c -o gups -lpthread


clean:
	rm -f gups *.o
