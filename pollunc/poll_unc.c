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
#include "SKX_IMC_BDF_Offset.h"

#define LOG_SIZE 1000000
#define DURATION_SECS 10

#define SOCKET 0                    // NUMA node/socket of interest
#define STACK 2                     // IIO stack of interest
int imc_channels[] = {0, 3};       // list of IMC channels to monitor
#define NUM_IMC_CHANNELS 2			// number of IMC channels in above list to monitor
#define NUM_CHA_BOXES 1             // CHA boxes 0-(NUM_CHA_BOXES-1) are monitored

// Counters to measure
uint64_t imc_counters[] = {0x00400304}; // CAS_COUNT.RD
#define NUM_IMC_COUNTERS 1
uint64_t cha_counters[] = {0x0040035a, 0x00403535}; // IRQ + PRQ occupancy, inserts
#define NUM_CHA_COUNTERS 0
#define CHA_FILTER0 0x00000000 // default; no filtering
#define CHA_FILTER1 0x10c48833 // Filter on WbMtoI + Black lemon
uint64_t iio_counters[] = {0x0040040F};
#define NUM_IIO_COUNTERS 0
#define NUM_COUNTERS (NUM_IMC_COUNTERS + NUM_CHA_COUNTERS + NUM_IIO_COUNTERS)

// #define RD_CAS_RANK0 0x004000b0
// #define WPQ_OCCUPANCY 0x00400081
// #define IRP_OCC_VAL 0x0040040F

// IIO counters are MSR-based
#define IRP_MSR_PMON_CTL_BASE 0x0A5BL
#define IRP_MSR_PMON_CTR_BASE 0x0A59L
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


int TSC_ratio;
unsigned int *mmconfig_ptr;         // must be pointer to 32-bit int so compiler will generate 32-bit loads and stores

int msr_fd;

FILE *log_file;

uint64_t prev_imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];
uint64_t cur_imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];
uint64_t prev_cha_counts[NUM_CHA_BOXES][NUM_CHA_COUNTERS];
uint64_t cur_cha_counts[NUM_CHA_BOXES][NUM_CHA_COUNTERS];
uint64_t prev_iio_counts[NUM_IIO_COUNTERS];
uint64_t cur_iio_counts[NUM_IIO_COUNTERS];

struct log_entry{
	uint64_t td_ns; //latest TSC
	uint64_t counts[NUM_COUNTERS];
};

struct log_entry LOG[LOG_SIZE];
uint32_t log_index = 0;
uint32_t counter = 0;
uint64_t prev_rdtsc = 0;
uint64_t cur_rdtsc = 0;
uint64_t tsc_sample = 0;
uint64_t end_rdtsc = 0;
uint64_t rc64;


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

// Convert PCI(bus:device.function,offset) to uint32_t array index
uint32_t PCI_cfg_index(unsigned int Bus, unsigned int Device, unsigned int Function, unsigned int Offset)
{
    uint32_t byteaddress;
    uint32_t index;
    // assert (Bus == BUS);
    assert (Device >= 0);
    assert (Function >= 0);
    assert (Offset >= 0);
    assert (Device < (1<<5));
    assert (Function < (1<<3));
    assert (Offset < (1<<12));

    // fprintf(log_file,"Bus,(Bus<<20)=%x\n",Bus,(Bus<<20));
    // fprintf(log_file,"Device,(Device<<15)=%x\n",Device,(Device<<15));
    // fprintf(log_file,"Function,(Function<<12)=%x\n",Function,(Function<<12));
    // fprintf(log_file,"Offset,(Offset)=%x\n",Offset,Offset);

    byteaddress = (Bus<<20) | (Device<<15) | (Function<<12) | Offset;
    index = byteaddress / 4;
    return ( index );
}

static void update_log(){
	int i, j, idx;
    uint64_t agg_count;
    LOG[log_index].td_ns = ((cur_rdtsc - prev_rdtsc) * 10) / TSC_ratio;
    // All counters are summed across space dimensions (channels for imc / cha boxes for cha)
    idx = 0;
    for(i = 0; i < NUM_IMC_COUNTERS; i++) {
        agg_count = 0;
        for(j = 0; j < NUM_IMC_CHANNELS; j++) {
            agg_count += (cur_imc_counts[j][i] - prev_imc_counts[j][i]);
        }
        LOG[log_index].counts[idx] = agg_count;
        idx += 1;
    }
    for(i = 0; i < NUM_CHA_COUNTERS; i++) {
        agg_count = 0;
        for(j = 0; j < NUM_CHA_BOXES; j++) {
            agg_count += (cur_cha_counts[j][i] - prev_cha_counts[j][i]);
        }
        LOG[log_index].counts[idx] = agg_count;
        idx += 1;
    }
    for(i = 0; i < NUM_IIO_COUNTERS; i++) {
        LOG[log_index].counts[idx] = cur_iio_counts[i] - prev_iio_counts[i];
        idx += 1;
    }
	log_index = (log_index + 1)%LOG_SIZE;
}

static void update_imc_config(void){
	//program the desired BDF values to measure IMC counters
    // Note: programs counters across call channels in given socket
    int bus, device, function, offset, imc, channel, subchannel, socket, rc;
    uint32_t index, value;
	int i = 0;

    socket = SOCKET;
    for(i = 0; i < NUM_IMC_CHANNELS; i++) {
        channel = imc_channels[i];
        for(counter = 0; counter < NUM_IMC_COUNTERS; counter++) {
            value = imc_counters[counter];

            bus = IMC_BUS_Socket[socket];
            device = IMC_Device_Channel[channel];
            function = IMC_Function_Channel[channel];
            offset = IMC_PmonCtl_Offset[counter];

            index = PCI_cfg_index(bus, device, function, offset);
            mmconfig_ptr[index] = value;
        }
    }
}

static void update_iio_config(void) {

    uint64_t msr_num;
    ssize_t ret;
    int counter;
    
    for(counter = 0; counter < NUM_IIO_COUNTERS; counter++) {
        msr_num = IRP_MSR_PMON_CTL_BASE + (0x20 * STACK) + counter;
        uint64_t msr_val = iio_counters[counter];
        ret = pwrite(msr_fd, &msr_val,sizeof(msr_val), msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }
    }
}

static void update_cha_config(void) {
    // Program CHA control registers
    ssize_t ret;
    uint64_t msr_num, msr_val;
    int cha, counter;

    for(cha = 0; cha < NUM_CHA_BOXES; cha++) {
        for(counter = 0; counter < NUM_CHA_COUNTERS; counter++) {
            msr_num = CHA_MSR_PMON_CTL_BASE + (0x10 * cha) + counter;
            msr_val = cha_counters[counter];
            ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
            if (ret != 8) {
                printf("ERROR writing to MSR device, write %ld bytes\n", ret);
                exit(-1);
            }
        }
        
        // Filters
        msr_num = CHA_MSR_PMON_FILTER0_BASE + (0x10 * cha); // Filter0
        msr_val = CHA_FILTER0;
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }

        msr_num = CHA_MSR_PMON_FILTER1_BASE + (0x10 * cha); // Filter1
        msr_val = CHA_FILTER1;
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }
    }
}

static void sample_imc_counters(){
    int bus, device, function, offset, imc, channel, subchannel, counter, i;
    uint32_t index, low, high;
    uint64_t count;

    for(i = 0; i < NUM_IMC_CHANNELS; i++) {
        bus = IMC_BUS_Socket[SOCKET];
        channel = imc_channels[i];
        device = IMC_Device_Channel[channel];
        function = IMC_Function_Channel[channel];
        for(counter = 0; counter < NUM_IMC_COUNTERS; counter++) {
            offset = IMC_PmonCtr_Offset[counter];
            index = PCI_cfg_index(bus, device, function, offset);
            low = mmconfig_ptr[index];
            high = mmconfig_ptr[index+1];
            count = ((uint64_t) high) << 32 | (uint64_t) low;
            prev_imc_counts[i][counter] = cur_imc_counts[i][counter];
            cur_imc_counts[i][counter] = count; 
        }
    }
}

static void sample_irp_counters(void) {
    ssize_t ret;
    uint64_t msr_num, msr_val;
    int counter;

    for(counter = 0; counter < NUM_IIO_COUNTERS; counter++) {
        msr_num = IRP_MSR_PMON_CTR_BASE + (0x20 * STACK) + counter;
        ret = pread(msr_fd, &msr_val, sizeof(msr_val), msr_num);
        if (ret != sizeof(msr_val)) {
            printf("ERROR: failed to read MSR %lx", msr_num);
            exit(-1);
        }
        prev_iio_counts[counter] = cur_iio_counts[counter];
        cur_iio_counts[counter] = msr_val;
    }
}

static void sample_cha_counters(void) {
    int cha, counter;
    uint64_t msr_num, msr_val;
    ssize_t ret;

    for (cha=0; cha<NUM_CHA_BOXES; cha++) {
        for (counter=0; counter<NUM_CHA_COUNTERS; counter++) {
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

static void sample_time_counter(){
    tsc_sample = rdtscp();
	prev_rdtsc = cur_rdtsc;
	cur_rdtsc = tsc_sample;
}

static void sample_counters(){
    if(NUM_IMC_COUNTERS > 0)
        sample_imc_counters();
    if(NUM_CHA_COUNTERS > 0)
        sample_cha_counters();
    if(NUM_IIO_COUNTERS > 0)
        sample_irp_counters();

	//sample time at the last
	sample_time_counter();
	return;
}



void main_exit() {
    //dump log info
    int i=0, j;
    while(i<LOG_SIZE) {
        fprintf(log_file, "%d %ld", i, LOG[i].td_ns);
        for(j = 0; j < NUM_COUNTERS; j++) {
            fprintf(log_file, " %ld", LOG[i].counts[j]);
        }
        fprintf(log_file, "\n");
        i++;
    }
}

static void catch_function(int signal) {
	printf("Caught SIGCONT. Shutting down...\n");

    main_exit();
	exit(0);
}

int main(){
    if (signal(SIGINT, catch_function) == SIG_ERR) {
		fprintf(stderr, "An error occurred while setting the signal handler.\n");
		return EXIT_FAILURE;
	}

    printf("Started\n");

    // Open MSR fd for this core
    int cpu = get_core_number();
    ssize_t ret;
    uint64_t msr_val;
    // Open MSR file for this core
    char filename[100];
    sprintf(filename, "/dev/cpu/%d/msr", cpu);
    msr_fd = open(filename, O_RDWR);
    if(msr_fd == -1) {
        printf("An error occurred while opening msr file.\n");
		return EXIT_FAILURE;
    }
    printf("Opened MSR fd\n");

    // Get TSC ratio
    ret = pread(msr_fd, &msr_val, sizeof(msr_val), 0xCEL);
    TSC_ratio = (msr_val & 0x000000000000ff00L) >> 8;
    printf("Read TSC ratio\n");


    sprintf(filename, "log.unc");
    log_file = fopen(filename, "w+");
    if (log_file == 0) {
        fprintf(stderr,"ERROR %s when trying to open log file %s\n",strerror(errno),filename);
        exit(-1);
    }
    printf("Opened log file\n");

    int mem_fd;
    unsigned long mmconfig_base=0x80000000;		// DOUBLE-CHECK THIS ON NEW SYSTEMS!!!!!   grep MMCONFIG /proc/iomem | awk -F- '{print $1}'
    unsigned long mmconfig_size=0x10000000;
    sprintf(filename,"/dev/mem");
	mem_fd = open(filename, O_RDWR);
	// fprintf(log_file,"   open command returns %d\n",mem_fd);
	if (mem_fd == -1) {
		fprintf(log_file,"ERROR %s when trying to open %s\n",strerror(errno),filename);
		exit(-1);
	}
	int map_prot = PROT_READ | PROT_WRITE;
	mmconfig_ptr = mmap(NULL, mmconfig_size, map_prot, MAP_SHARED, mem_fd, mmconfig_base);
    if (mmconfig_ptr == MAP_FAILED) {
        fprintf(log_file,"cannot mmap base of PCI configuration space from /dev/mem: address %lx\n", mmconfig_base);
        exit(2);
    }
    close(mem_fd);      // OK to close file after mmap() -- the mapping persists until unmap() or program exit
    printf("mmaped memfd\n");
    // fprintf(log_file,"Core no: %d\n",cpu);

    //initialize the log
    int i = 0, j = 0;
    while(i < LOG_SIZE){
        LOG[i].td_ns = 0;
        for(j = 0; j < NUM_COUNTERS; j++) {
            LOG[i].counts[j] = 0;
        }
        i++;
    }
    log_index = 0;
    printf("init log\n");

    update_imc_config();
    printf("updated imc config\n");
    update_cha_config();
    printf("updated cha config\n");
    update_iio_config();
    printf("updated iio config\n");

    sample_time_counter();
    end_rdtsc = cur_rdtsc + DURATION_SECS*TSC_ratio*100*1e6;
    
    while(cur_rdtsc < end_rdtsc){
        sample_counters();
        update_log();
        counter++;
    }

    main_exit();
    return 0;
}
