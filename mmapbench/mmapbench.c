# include <stdio.h>
# include <unistd.h>
# include <math.h>
# include <float.h>
# include <limits.h>
# include <sys/time.h>
#include <time.h>
#include <stdint.h>
#include <string.h>
 #define _GNU_SOURCE
#include <sys/mman.h>
#include <immintrin.h>
#include <fcntl.h>

#define MAP_HUGE_1GB (30 << MAP_HUGE_SHIFT)

#define CHUNK_SIZE 256*1024*1024LL
#define PAGE_SIZE 4096

double mysecond()
{
/* struct timeval { long        tv_sec;
            long        tv_usec;        };

struct timezone { int   tz_minuteswest;
             int        tz_dsttime;      };     */

        struct timeval tp;
        struct timezone tzp;
        int i;

        i = gettimeofday(&tp,&tzp);
        return ( (double) tp.tv_sec + (double) tp.tv_usec * 1.e-6 );
}

// Read one byte from each page
double WORKLOAD_ReadOneByte(void *p, size_t len, uint64_t *read_checksum) {
    int j;
    char *a = (char *) p;
    for(j = 0; j < len; j += PAGE_SIZE) {
        *read_checksum += a[j]; 
    }
    return len;
}

// Write one byte to each page
double WORKLOAD_WriteOneByte(void *p, size_t len, uint64_t *read_checksum) {
    int j;
    char *a = (char *) p;
    for(j = 0; j < len; j += PAGE_SIZE) {
        a[j] = (char)111;
    }
    return len;
}

// Read all data in each page once
double WORKLOAD_ReadAll64(void *p, size_t len, uint64_t *read_checksum) {
    int j;
    char *a = (char *) p;
	__m512i sum = _mm512_set_epi32(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
	for (j=0; j<len; j += 64) {
		__m512i mm_a = _mm512_load_si512(&a[j]);
		sum = _mm512_add_epi32(sum, mm_a);
	}

	int chx0, chx1, chx2, chx3;
	__m128i chx;
	chx = _mm512_extracti32x4_epi32(sum, 0);
	chx0 = _mm_extract_epi32(chx, 0);
	chx1 = _mm_extract_epi32(chx, 1);
	chx2 = _mm_extract_epi32(chx, 2);
	chx3 = _mm_extract_epi32(chx, 3);
	*read_checksum += chx0 + chx1 + chx2 + chx3;
	chx = _mm512_extracti32x4_epi32(sum, 1);
	chx0 = _mm_extract_epi32(chx, 0);
	chx1 = _mm_extract_epi32(chx, 1);
	chx2 = _mm_extract_epi32(chx, 2);
	chx3 = _mm_extract_epi32(chx, 3);
	*read_checksum += chx0 + chx1 + chx2 + chx3;
	chx = _mm512_extracti32x4_epi32(sum, 2);
	chx0 = _mm_extract_epi32(chx, 0);
	chx1 = _mm_extract_epi32(chx, 1);
	chx2 = _mm_extract_epi32(chx, 2);
	chx3 = _mm_extract_epi32(chx, 3);
	*read_checksum += chx0 + chx1 + chx2 + chx3;
	chx = _mm512_extracti32x4_epi32(sum, 3);
	chx0 = _mm_extract_epi32(chx, 0);
	chx1 = _mm_extract_epi32(chx, 1);
	chx2 = _mm_extract_epi32(chx, 2);
	chx3 = _mm_extract_epi32(chx, 3);
	*read_checksum += chx0 + chx1 + chx2 + chx3;
	return len;
}

// Write to all bytes in each page once
double WORKLOAD_WriteAll64(void *p, size_t len, uint64_t *read_checksum) {
    int j;
    char *a = (char *) p;
	__m512i val = _mm512_set_epi32(1995, 1995, 2002, 2002, 1995, 1995, 2002, 2002, 1995, 1995, 2002, 2002, 1995, 1995, 2002, 2002);
	for (j=0; j<len; j += 64) {
		_mm512_store_si512(&a[j], val);
	}

	return len;
}




int main(int argc, char **argv) {

    if(argc != 6) {
		printf("Invalid args. Usage: ./mmapbench <workload> <duration-in-secs> <filepath> <fileoffset> <filelength>\n");
		exit(-1);
	}

	char *workload = argv[1];
	int duration = atoi(argv[2]);
    char *fpath = argv[3];
    size_t foffset, flen;
    if(sscanf(argv[4], "%zu", &foffset) != 1) {
        printf("Unable to parse offset\n");
        exit(-1);
    }
    if(sscanf(argv[5], "%zu", &flen) != 1) {
        printf("Unable to parse length\n");
        exit(-1);
    }

    // Which workload?
    double (*execute)(void *, size_t, uint64_t *) = NULL;
    int workload_writes = 0;
	if(strcmp(workload, "ReadOneByte") == 0) {
		execute = &WORKLOAD_ReadOneByte;
	} else if(strcmp(workload, "WriteOneByte") == 0) {
		execute = &WORKLOAD_WriteOneByte;
        workload_writes = 1;
	} else if(strcmp(workload, "ReadAll64") == 0) {
		execute = &WORKLOAD_ReadAll64;
	} else if(strcmp(workload, "WriteAll64") == 0) {
		execute = &WORKLOAD_WriteAll64;
        workload_writes = 1;
	} else {
		printf("Unknown workload\n");
		exit(-1);
	}

    // mmap file
    void *memarea = NULL;
    int fd;
    fd = open(fpath, (workload_writes)?(O_RDWR):(O_RDONLY));
    if(fd < 0) {
        printf("File open failed\n");
        exit(-1);
    }
    int prot;
    prot = PROT_READ;
    if(workload_writes) {
        prot  = (prot | PROT_WRITE);
    }
    memarea = mmap(NULL, flen, prot, MAP_SHARED, fd, foffset);
    if(memarea == MAP_FAILED) {
        printf("mmap failed\n");
        exit(-1);
    }

    // madvise
    if(madvise(memarea, flen, MADV_SEQUENTIAL) < 0) {
        printf("madvise failed\n");
        exit(-1);
    }

    // if(madvise(memarea, flen, MADV_HUGEPAGE) < 0) {
    //     printf("madv hugepage failed\n");
    //     exit(-1);
    // } 

	

	double start_tim = mysecond();
	double total_bytes = 0.0;
	double actual_duration;
	uint64_t read_checksum = 0;
    size_t chunk_size = CHUNK_SIZE;
    size_t cur_offset = 0;
	while(1) {
		
		total_bytes += (*execute)((char *)memarea + cur_offset, (chunk_size < flen - cur_offset)?(chunk_size):(flen-cur_offset), &read_checksum);

		double cur_tim = mysecond();
		if(cur_tim - start_tim >= duration) {
			actual_duration = cur_tim - start_tim;
			break;
		}

        cur_offset += chunk_size;
        if(cur_offset >= flen) {
            cur_offset = 0;
        }
	}

	double arr_checksum = 0.0;
	// Read random offset in memarea (just to make sure compiler does not optimize away writes)
    srand(time(0));
    arr_checksum += (double)((char *) memarea)[rand() % flen];

	printf("Read checksum %lu\n", read_checksum);
	printf("Array checksum %lf\n", arr_checksum);
	printf("Throughput (GB/s): %lf\n", total_bytes/actual_duration/1e9);

    return 0;
}