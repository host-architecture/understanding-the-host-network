#include <stdio.h>				// printf, etc
#include <stdint.h>				// standard integer types, e.g., uint32_t
#include <signal.h>				// for signal handler
#include <stdlib.h>				// exit() and EXIT_FAILURE
#include <string.h>				// strerror() function converts errno to a text string for printing
#include <fcntl.h>				// for open()
#include <errno.h>				// errno support
#include <assert.h>				// assert() function
#include <unistd.h>				// sysconf() function, sleep() function
#include <sys/mman.h>			// support for mmap() function
#include <math.h>				// for pow() function used in RAPL computations
#include <time.h>
#include <stdbool.h>
#include <sys/time.h>			// for gettimeofday
#include <sys/ipc.h>
#include <sys/shm.h>

// CHA counters are MSR-based.  
//   The starting MSR address is 0x0E00 + 0x10*CHA
//   	Offset 0 is Unit Control -- mostly un-needed
//   	Offsets 1-4 are the Counter PerfEvtSel registers
//   	Offset 5 is Filter0	-- selects state for LLC lookup event (and TID, if enabled by bit 19 of PerfEvtSel)
//   	Offset 6 is Filter1 -- lots of filter bits, including opcode -- default if unused should be 0x03b, or 0x------33 if using opcode matching
//   	Offset 7 is Unit Status
//   	Offsets 8,9,A,B are the Counter count registers
#define CHA_MSR_PMON_BASE 0x0E00L
#define CHA_MSR_PMON_CTL_BASE 0x0E01L
#define CHA_MSR_PMON_FILTER0_BASE 0x0E05L
#define CHA_MSR_PMON_FILTER1_BASE 0x0E06L
#define CHA_MSR_PMON_STATUS_BASE 0x0E07L
#define CHA_MSR_PMON_CTR_BASE 0x0E08L

#define SAMPLE_INTERVAL_SECS 1

#define CORE 31
#define NUM_LPROCS 64
#define SOCKET 3
#define NUM_CHA_BOXES 18
#define NUM_CHA_COUNTERS 4

#define NUMA0_CORE 28
#define NUMA1_CORE 29
#define NUMA2_CORE 30
#define NUMA3_CORE 31

// Filter1 values for transactions
// DRd: 0x40433
// WbEFtoI: 0x48c33
// WbMtoI: 0x48833
// ItoM: 0x49033
// BlackLemon(0x218): 0x43033


int TSC_ratio;

uint64_t cha_counts[NUM_CHA_BOXES][NUM_CHA_COUNTERS];
uint64_t prev_cha_counts[NUM_CHA_BOXES][NUM_CHA_COUNTERS];
uint64_t cur_cha_counts[NUM_CHA_BOXES][NUM_CHA_COUNTERS];


uint64_t prev_rdtsc = 0;
uint64_t cur_rdtsc = 0;

int msr_fd;


static inline __attribute__((always_inline)) unsigned long rdtsc()
{
   unsigned long a, d;

   __asm__ volatile("rdtsc" : "=a" (a), "=d" (d));

   return (a | (d << 32));
}


static inline __attribute__((always_inline)) unsigned long rdtscp()
{
   unsigned long a, d, c;

   __asm__ volatile("rdtscp" : "=a" (a), "=d" (d), "=c" (c));

   return (a | (d << 32));
}

extern inline __attribute__((always_inline)) int get_core_number()
{
   unsigned long a, d, c;

   __asm__ volatile("rdtscp" : "=a" (a), "=d" (d), "=c" (c));

   return ( c & 0xFFFUL );
}

// msr_fd must be open before executing this function
static void sample_cha_counters(void) {
    int cha, counter;
    uint64_t msr_num, msr_val;
    ssize_t ret;
    for (cha=0; cha<NUM_CHA_BOXES; cha++) {
        for (counter=0; counter<1; counter++) { // NOTE: Reading only counter 0 for now
            msr_num = CHA_MSR_PMON_CTR_BASE + (0x10 * cha) + counter;
            ret = pread(msr_fd, &msr_val, sizeof(msr_val), msr_num);
            if (ret != sizeof(msr_val)) {
                printf("ERROR: failed to read MSR %lx", msr_num);
                exit(-1);
            }
            prev_cha_counts[cha][counter] = cur_cha_counts[cha][counter];
            cur_cha_counts[cha][counter] = msr_val;
        }
	}
}

static void catch_function(int signal) {
	exit(0);
}

int main(int argc, char** argv){
    if (signal(SIGINT, catch_function) == SIG_ERR) {
		printf("An error occurred while setting the signal handler.\n");
		return EXIT_FAILURE;
	}

    if(argc < 2) {
        printf("Insufficient arguments\n");
        printf("USAGE: ./sample_cha <event> [opcode]\n");
        return EXIT_FAILURE;
    }

    uint64_t cha_event = 0x00400000;
    uint64_t cha_filter0 = 0x00000000;
    uint64_t cha_filter1 = 0x0000003B;

    sscanf(argv[1], "%lx", &cha_event);
    // if(argc >= 3) {
    //     sscanf(argv[2], "%lx", &cha_filter0);
    // }
    // if(argc >= 4) {
    //     sscanf(argv[3], "%lx", &cha_filter1);
    // }
    if(argc >= 3) {
        // opcode filtering
        uint64_t opc0;
        sscanf(argv[2], "%lx", &opc0);
        cha_filter1 = (0x00000033 | (opc0 << 9));
        // uint64_t opc1 = 0x218; // Black lemon
        //uint64_t opc1 = 0x200; // RFO
	//uint64_t opc1 = 0;
        //cha_filter1 = (cha_filter1 | (opc1 << 19)); 
        printf("Filter1: 0x%lx\n", cha_filter1);
    }

    int cpu = get_core_number();
    // fprintf(log_file,"Core no: %d\n",cpu);

    // Open MSR file for this core
    char filename[100];
    sprintf(filename, "/dev/cpu/%d/msr", cpu);
    msr_fd = open(filename, O_RDWR);
    if(msr_fd == -1) {
        printf("An error occurred while opening msr file.\n");
		return EXIT_FAILURE;
    }

    ssize_t ret;
    uint64_t msr_num, msr_val;

    // Get TSC frequency
    ret = pread(msr_fd, &msr_val, sizeof(msr_val), 0xCEL);
    TSC_ratio = (msr_val & 0x000000000000ff00L) >> 8;

    // Program CHA control registers
    int cha;
    for(cha = 0; cha < NUM_CHA_BOXES; cha++) {
        msr_num = CHA_MSR_PMON_CTL_BASE + (0x10 * cha) + 0; // counter 0
        msr_val = cha_event;
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }

        // Filters
        msr_num = CHA_MSR_PMON_FILTER0_BASE + (0x10 * cha); // Filter0
        msr_val = cha_filter0;
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }

        msr_num = CHA_MSR_PMON_FILTER1_BASE + (0x10 * cha); // Filter1
        msr_val = cha_filter1;
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }
    }

    // Sample CHA counters
    prev_rdtsc = rdtscp();
    sample_cha_counters();
    while(1) {
        cur_rdtsc = rdtscp();
        if(cur_rdtsc > prev_rdtsc + SAMPLE_INTERVAL_SECS*TSC_ratio*100*1e6) {
            sample_cha_counters();
            for(cha = 0; cha < NUM_CHA_BOXES; cha++) {
                // sampling only counter 0 for now
                printf("%lu ", cur_cha_counts[cha][0] - prev_cha_counts[cha][0]);
            }
            printf("\n");
            fflush(stdout);
            prev_rdtsc = cur_rdtsc;
        }
    }

    return 0;
}
