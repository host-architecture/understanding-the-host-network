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

// #define LOG_FREQUENCY 1
// #define LOG_PRINT_FREQUENCY 20
#define LOG_SIZE 1000000
#define DURATION_SECS 10

#define CORE 31
#define NUM_LPROCS 64
#define SOCKET 3
#define CHANNEL 0
# define NUM_IMC_CHANNELS 6			// includes channels on all IMCs in a socket
# define NUM_IMC_COUNTERS 4			// 0-3 are the 4 programmable counters, 4 is the fixed-function DCLK counter
#define NUM_IMC 2

#define NUMA0_CORE 28
#define NUMA1_CORE 29
#define NUMA2_CORE 30
#define NUMA3_CORE 31

#define RD_CAS_RANK0 0x004000b0
#define WPQ_OCCUPANCY 0x00400081
#define IRP_MSR_PMON_CTL_BASE 0x0A5BL
#define IRP_MSR_PMON_CTR_BASE 0x0A59L
#define STACK 1
#define IRP_OCC_VAL 0x0040040F

#define NUM_CHA_BOXES 1
#define NUM_CHA_COUNTERS 4

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

uint64_t imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];
uint64_t prev_imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];
uint64_t cur_imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];

struct log_entry{
	uint64_t l_tsc; //latest TSC
	uint64_t td_ns; //latest measured time delta in us
	int cpu; //current cpu
	uint32_t bank0_count;
    uint32_t bank1_count;
    uint32_t bank2_count;
    uint32_t bank3_count;
};

struct log_entry LOG[LOG_SIZE];
uint32_t log_index = 0;
uint32_t counter = 0;
uint64_t prev_rdtsc = 0;
uint64_t cur_rdtsc = 0;
uint64_t tsc_sample = 0;
uint64_t end_rdtsc = 0;
uint64_t rc64;

uint32_t latest_bank0_count;
uint32_t latest_bank1_count;
uint32_t latest_bank2_count;
uint32_t latest_bank3_count;

uint64_t latest_time_delta_us = 0;
uint64_t latest_time_delta_ns = 0;

uint64_t prev_irp_occ_agg = 0;
uint64_t cur_irp_occ_agg = 0;
uint64_t prev_irp_ts = 0;
uint64_t cur_irp_ts = 0;

uint64_t prev_cha_counts[NUM_CHA_BOXES][NUM_CHA_COUNTERS];
uint64_t cur_cha_counts[NUM_CHA_BOXES][NUM_CHA_COUNTERS];
uint64_t prev_cha_count_agg[NUM_CHA_COUNTERS];
uint64_t cur_cha_count_agg[NUM_CHA_COUNTERS];

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

static void update_log(int c){
	LOG[log_index % LOG_SIZE].l_tsc = cur_rdtsc;
	LOG[log_index % LOG_SIZE].td_ns = ((cur_rdtsc - prev_rdtsc) * 10) / TSC_ratio;
	// LOG[log_index % LOG_SIZE].bank0_count = cur_irp_occ_agg - prev_irp_occ_agg;
    LOG[log_index % LOG_SIZE].bank0_count = cur_imc_counts[CHANNEL][0] - prev_imc_counts[CHANNEL][0];
    // LOG[log_index % LOG_SIZE].bank1_count = ((cur_irp_ts - prev_irp_ts) * 10) / TSC_ratio;
    // LOG[log_index % LOG_SIZE].bank2_count = cur_cha_count_agg[0] - prev_cha_count_agg[0];
    // LOG[log_index % LOG_SIZE].bank3_count = cur_cha_count_agg[1] - prev_cha_count_agg[1];
	// LOG[log_index % LOG_SIZE].cpu = c;
	log_index++;
}

static void update_imc_config(void){
	//program the desired BDF values to measure IMC counters
    // Note: programs counters across call channels in given socket
    int bus, device, function, offset, imc, channel, subchannel, socket, rc;
    uint32_t index, value;
	int i = 0;

    socket = SOCKET;
    for(imc = 0; imc < NUM_IMC; imc++) {
        for(subchannel = 0; subchannel < (NUM_IMC_CHANNELS/NUM_IMC); subchannel++) {
            for(counter = 0; counter < 1; counter++) { // NOTE: Programming only counter 0
                // umask is bank number. setting ith counter to read ith bank
                value = WPQ_OCCUPANCY;

                channel = 3*imc + subchannel;				// PCI device/function is indexed by channel here (0-5)
                bus = IMC_BUS_Socket[socket];
                device = IMC_Device_Channel[channel];
                function = IMC_Function_Channel[channel];
                offset = IMC_PmonCtl_Offset[counter];
                // fprintf(log_file,"DEBUG: translated bus/device/function/offset values %#x %#x %#x %#x\n",bus,device,function,offset);
                index = PCI_cfg_index(bus, device, function, offset);
                mmconfig_ptr[index] = value;
            }
        }
    }
}

static void update_iio_config(void) {

    uint64_t msr_num;
    ssize_t ret;
    msr_num = IRP_MSR_PMON_CTL_BASE + (0x20 * STACK) + 0;
    uint64_t msr_val = IRP_OCC_VAL;
    ret = pwrite(msr_fd, &msr_val,sizeof(msr_val), msr_num);
    if (ret != 8) {
        printf("ERROR writing to MSR device, write %ld bytes\n", ret);
        exit(-1);
    }
}

static void update_cha_config(void) {
    // Program CHA control registers
    ssize_t ret;
    uint64_t msr_num, msr_val;
    int cha;
    for(cha = 0; cha < NUM_CHA_BOXES; cha++) {
        msr_num = CHA_MSR_PMON_CTL_BASE + (0x10 * cha) + 0; // counter 0
        msr_val = 0x0040035a;
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }

        msr_num = CHA_MSR_PMON_CTL_BASE + (0x10 * cha) + 1; // counter 1
        msr_val = 0x00403535; // IRQ + PRQ inserts
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }

        // Filters
        msr_num = CHA_MSR_PMON_FILTER0_BASE + (0x10 * cha); // Filter0
        msr_val = 0x00000000; // default; no filtering
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }

        msr_num = CHA_MSR_PMON_FILTER1_BASE + (0x10 * cha); // Filter1
        msr_val = 0x10c48833; // Filter on WbMtoI + Black lemon
        ret = pwrite(msr_fd,&msr_val,sizeof(msr_val),msr_num);
        if (ret != 8) {
            printf("ERROR writing to MSR device, write %ld bytes\n", ret);
            exit(-1);
        }
    }
}

static void sample_imc_counters(){
    int bus, device, function, offset, imc, channel, subchannel, counter;
    uint32_t index, low, high;
    uint64_t count;

    bus = IMC_BUS_Socket[SOCKET];
    channel = CHANNEL;
    device = IMC_Device_Channel[channel];
    function = IMC_Function_Channel[channel];
    counter = 0; // sampling only counter 0
    offset = IMC_PmonCtr_Offset[counter];
    index = PCI_cfg_index(bus, device, function, offset);
    low = mmconfig_ptr[index];
    high = mmconfig_ptr[index+1];
    count = ((uint64_t) high) << 32 | (uint64_t) low;
    imc_counts[channel][counter] = count;
    prev_imc_counts[channel][counter] = cur_imc_counts[channel][counter];
    cur_imc_counts[channel][counter] = count; 
}

static void sample_irp_counters(void) {
    ssize_t ret;
    uint64_t msr_num, msr_val;
	msr_num = IRP_MSR_PMON_CTR_BASE + (0x20 * STACK) + 0;
    ret = pread(msr_fd, &msr_val, sizeof(msr_val), msr_num);
    if (ret != sizeof(msr_val)) {
        printf("ERROR: failed to read MSR %lx", msr_num);
        exit(-1);
    }
    prev_irp_occ_agg = cur_irp_occ_agg;
	cur_irp_occ_agg = msr_val;
    prev_irp_ts = cur_irp_ts;
    cur_irp_ts = rdtscp();
}

static void sample_cha_counters(void) {
    int cha, counter;
    uint64_t msr_num, msr_val;
    ssize_t ret;
    for(counter = 0; counter < 2; counter++) {
        prev_cha_count_agg[counter] = cur_cha_count_agg[counter];
        cur_cha_count_agg[counter] = 0;
    }
    for (cha=0; cha<NUM_CHA_BOXES; cha++) {
        for (counter=0; counter<2; counter++) { // Reading counters 0 and 1
            msr_num = CHA_MSR_PMON_CTR_BASE + (0x10 * cha) + counter;
            ret = pread(msr_fd, &msr_val, sizeof(msr_val), msr_num);
            if (ret != sizeof(msr_val)) {
                printf("ERROR: failed to read MSR %lx", msr_num);
                exit(-1);
            }
            prev_cha_counts[cha][counter] = cur_cha_counts[cha][counter];
            cur_cha_counts[cha][counter] = msr_val;
            cur_cha_count_agg[counter] += msr_val;
        }
	}
}

static void sample_time_counter(){
    tsc_sample = rdtscp();
	prev_rdtsc = cur_rdtsc;
	cur_rdtsc = tsc_sample;
}

static void sample_counters(int c){
    sample_imc_counters();
    // sample_irp_counters();
    // sample_cha_counters();

	//sample time at the last
	sample_time_counter();
	return;
}

static void update_bank_counts(void) {
    int channel;
	// latest_time_delta_ns = ((cur_rdtsc - prev_rdtsc) * 10) / 33;
    latest_time_delta_ns = ((cur_rdtsc - prev_rdtsc) * 10) / TSC_ratio;
    if(latest_time_delta_ns > 0) {
        channel = CHANNEL;
        latest_bank0_count = (cur_imc_counts[channel][0] - prev_imc_counts[channel][0]);
        latest_bank1_count = (cur_imc_counts[channel][1] - prev_imc_counts[channel][1]);
        latest_bank2_count = (cur_imc_counts[channel][2] - prev_imc_counts[channel][2]);
        latest_bank3_count = (cur_imc_counts[channel][3] - prev_imc_counts[channel][3]);
        
    }
}



void main_init() {
    //initialize the log
    int i=0;
    while(i<LOG_SIZE){
        LOG[i].l_tsc = 0;
        LOG[i].td_ns = 0;
        LOG[i].bank0_count = 0;
        LOG[i].bank1_count = 0;
        LOG[i].bank2_count = 0;
        LOG[i].bank3_count = 0;
        LOG[i].cpu = 65;
        i++;
    }
    printf("init log\n");

    update_imc_config();
    printf("updated imc config\n");
    update_iio_config();
    printf("updated iio config\n");
    update_cha_config();
    printf("updated cha config\n");
}

void main_exit() {
    //dump log info
    int i=0;
    fprintf(log_file,"index latest_tsc time_delta_ns bank0_count bank1_count bank2_count bank3_count\n");
    while(i<LOG_SIZE) {
        fprintf(log_file,"%d %ld %ld %d %d %d %d\n",
        i,
        LOG[i].l_tsc,
        LOG[i].td_ns,
        LOG[i].bank0_count,
        LOG[i].bank1_count,
        LOG[i].bank2_count,
        LOG[i].bank3_count
        );
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
		fprintf(log_file, "An error occurred while setting the signal handler.\n");
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


    sprintf(filename, "log.chaiio");
    log_file = fopen(filename,"w+");
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

    main_init();
    printf("main init complete\n");

    sample_time_counter();
    end_rdtsc = cur_rdtsc + DURATION_SECS*TSC_ratio*100*1e6;
    
    while(cur_rdtsc < end_rdtsc){
        sample_counters(cpu);
        //update_counts();
        update_log(cpu);
        counter++;
    }

    main_exit();
    return 0;
}