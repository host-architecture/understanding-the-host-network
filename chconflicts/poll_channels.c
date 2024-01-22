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
#define CHANNELA 0
#define CHANNELB 3
# define NUM_IMC_CHANNELS 6			// includes channels on all IMCs in a socket
# define NUM_IMC_COUNTERS 4			// 0-3 are the 4 programmable counters, 4 is the fixed-function DCLK counter
#define NUM_IMC 2

#define NUMA0_CORE 28
#define NUMA1_CORE 29
#define NUMA2_CORE 30
#define NUMA3_CORE 31

#define CAS_COUNT_RD 0x00400304

int TSC_ratio;
unsigned int *mmconfig_ptr;         // must be pointer to 32-bit int so compiler will generate 32-bit loads and stores

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
	LOG[log_index % LOG_SIZE].td_ns = latest_time_delta_ns;
	LOG[log_index % LOG_SIZE].bank0_count = latest_bank0_count;
    LOG[log_index % LOG_SIZE].bank1_count = latest_bank1_count;
	LOG[log_index % LOG_SIZE].cpu = c;
	log_index++;
}

static void update_imc_config(void){
	//program the desired BDF values to measure IMC counters
    // Note: programs counters across call channels in given socket
    int bus, device, function, offset, imc, channel, subchannel, socket, rc;
    uint32_t index, value;
    FILE* input_file;
    char filename[100];
    char description[32];
	sprintf(filename,"imc_perfevtsel.input");
	input_file = fopen(filename,"r");
	if (input_file == 0) {
		fprintf(log_file,"ERROR %s when trying to open Uncore PCI PerfEvtSel input file %s\n",strerror(errno),filename);
		exit(-1);
	}
	int i = 0;

    socket = SOCKET;
    for(imc = 0; imc < NUM_IMC; imc++) {
        for(subchannel = 0; subchannel < (NUM_IMC_CHANNELS/NUM_IMC); subchannel++) {
            for(counter = 0; counter < 1; counter++) {
                value = CAS_COUNT_RD;

                channel = 3*imc + subchannel;				// PCI device/function is indexed by channel here (0-5)
                bus = IMC_BUS_Socket[socket];
                device = IMC_Device_Channel[channel];
                function = IMC_Function_Channel[channel];
                offset = IMC_PmonCtl_Offset[counter];
                // fprintf(log_file,"DEBUG: translated bus/device/function/offset values %#x %#x %#x %#x\n",bus,device,function,offset);
                index = PCI_cfg_index(bus, device, function, offset);
                mmconfig_ptr[index] = value;
                // printf("updated channel %d counter %d config %d\n", channel, counter, value);
            }
        }
    }
}

static void sample_imc_counters(){
    int bus, device, function, offset, imc, channel, subchannel, counter;
    uint32_t index, low, high;
    uint64_t count;

    for(channel=0; channel<NUM_IMC_CHANNELS; channel++) {
        bus = IMC_BUS_Socket[SOCKET];
        device = IMC_Device_Channel[channel];
        function = IMC_Function_Channel[channel];
        if(channel != CHANNELA && channel != CHANNELB) {
            continue;
        }
        for (counter=0; counter<1; counter++) {
            offset = IMC_PmonCtr_Offset[counter];
            index = PCI_cfg_index(bus, device, function, offset);
            low = mmconfig_ptr[index];
            high = mmconfig_ptr[index+1];
            count = ((uint64_t) high) << 32 | (uint64_t) low;
            imc_counts[channel][counter] = count;
            prev_imc_counts[channel][counter] = cur_imc_counts[channel][counter];
            cur_imc_counts[channel][counter] = count;
            // printf("channel: %d counter %d val=%lu\n", channel, counter, count);
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

	//sample time at the last
	sample_time_counter();
	return;
}

static void update_bank_counts(void) {
    int channel;
	// latest_time_delta_ns = ((cur_rdtsc - prev_rdtsc) * 10) / 33;
    latest_time_delta_ns = ((cur_rdtsc - prev_rdtsc) * 10) / TSC_ratio;
    if(latest_time_delta_ns > 0) {
        latest_bank0_count = (cur_imc_counts[CHANNELA][0] - prev_imc_counts[CHANNELA][0]);
        latest_bank1_count = (cur_imc_counts[CHANNELB][0] - prev_imc_counts[CHANNELB][0]);
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

    update_imc_config();
}

void main_exit() {
    //dump log info
    int i=0;
    fprintf(log_file,"index latest_tsc time_delta_ns ch0_count ch1_count\n");
    while(i<LOG_SIZE) {
        fprintf(log_file,"%d %lld %lld %d %d\n",
        i,
        LOG[i].l_tsc,
        LOG[i].td_ns,
        LOG[i].bank0_count,
        LOG[i].bank1_count
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

    // Get TSC frequency
    int msr_fd;
    ssize_t ret;
    uint64_t msr_val;
    msr_fd = open("/dev/cpu/0/msr", O_RDWR);
    if(msr_fd == -1) {
        fprintf(log_file, "An error occurred while opening msr file.\n");
		return EXIT_FAILURE;
    }
    ret = pread(msr_fd, &msr_val, sizeof(msr_val), 0xCEL);
    TSC_ratio = (msr_val & 0x000000000000ff00L) >> 8;


    char filename[100];
    sprintf(filename,"log.chconf");
    log_file = fopen(filename,"w+");
    if (log_file == 0) {
        fprintf(stderr,"ERROR %s when trying to open log file %s\n",strerror(errno),filename);
        exit(-1);
    }

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


    int cpu = get_core_number();
    // fprintf(log_file,"Core no: %d\n",cpu);

    main_init();

    sample_time_counter();
    end_rdtsc = cur_rdtsc + DURATION_SECS*TSC_ratio*100*1e6;
    
    while(cur_rdtsc < end_rdtsc){
        sample_counters(cpu);
        update_bank_counts();
        update_log(cpu);
        counter++;
    }

    main_exit();
    return 0;
}