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
// #define IRP_MSR_PMON_CTL_BASE 0x0A5BL
// #define IRP_MSR_PMON_CTR_BASE 0x0A59L
// #define STACK 2 //We're concerned with stack #2 on our machine
// #define IRP_OCC_VAL 0x0040040F
#define PQOS_MSR_MBA_MASK_START 0xD50L
// #define PQOS_MSR_MBA_MASK_START 0x1A4
#define IIO_PCIE_1_PORT_0_BW_IN 0x0B20 //We're concerned with PCIe 1 stack on our machine (Table 1-11 in Intel Skylake Manual)

#define CORE 28
#define NUM_LPROCS 64
#define SOCKET 0
# define NUM_IMC_CHANNELS 6			// includes channels on all IMCs in a socket
# define NUM_IMC_COUNTERS 2			// 0-3 are the 4 programmable counters, 4 is the fixed-function DCLK counter

#define NUMA0_CORE 28
#define NUMA1_CORE 29
#define NUMA2_CORE 30
#define NUMA3_CORE 31
#define MBA_COS_ID 1

#define SH_MEM 1
#if SH_MEM
#define SHM_MMAP 1
#if SHM_MMAP
char *p = NULL;
#endif
int shm_fd;  
int shm_ret;
#define DEVICE_FILENAME "/dev/mchar"  
char str_to_write[64];
#endif

#define MBA_CTRL 1
#define MBA_TIMEOUT_US 80 // MBA timeout in microseconds
#define MBA_STOP_US 70
//TODO: Add a mechanism to ensure MBA_TIMEOUT_US > MBA_STOP_US
#define IIO_THRESHOLD 70
#define PCIE_BW_THRESHOLD 84
#define BW_TOLERANCE 0

#define MBA_TEST 0
#define USE_PROCESS_SCHEDULER 1

#define MBA_VAL_HIGH 90
#define MBA_VAL_LOW 0
#define THRESH_NUM_SAMPLES 8

int msr_fd[NUM_LPROCS];		// msr device driver files will be read from various functions, so make descriptors global
unsigned int *mmconfig_ptr;         // must be pointer to 32-bit int so compiler will generate 32-bit loads and stores

FILE *log_file;

uint64_t imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];
uint64_t prev_imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];
uint64_t cur_imc_counts[NUM_IMC_CHANNELS][NUM_IMC_COUNTERS];

struct log_entry{
	uint64_t l_tsc; //latest TSC
	uint64_t td_ns; //latest measured time delta in us
	float l_avg_rd_bw; //latest measured avg IIO occupancy
	float l_avg_wr_bw; //latest calculated smoothed occupancy
	int cpu; //current cpu
	uint32_t l_mba_val; //IP datagram length at last sample
    uint32_t l_measured_avg_occ;
    float l_measured_avg_occ_thresh_avg;
    uint32_t l_measured_avg_pcie_bw;
    uint32_t l_measured_lat_pcie_bw;
    uint32_t l_red_timeout;
};

struct log_entry LOG[LOG_SIZE];
uint32_t log_index = 0;
uint32_t counter = 0;
uint64_t prev_rdtsc = 0;
uint64_t cur_rdtsc = 0;
// uint64_t prev_cum_occ = 0;
// uint64_t cur_cum_occ = 0;
uint64_t tsc_sample = 0;
uint64_t msr_num;
uint64_t msr_val;
uint64_t rc64;
// uint64_t cum_occ_sample = 0;
// uint64_t latest_avg_occ = 0;
float latest_avg_rd_bw = 0;
float latest_avg_wr_bw = 0;
uint32_t latest_mba_val = 0;
uint64_t latest_time_delta = 0;
// uint64_t smoothed_avg_occ = 0;
// float smoothed_avg_occ_f = 0.0;
uint64_t latest_time_delta_us = 0;
uint64_t latest_time_delta_ns = 0;
// uint32_t latest_datagram_len = 0;
uint32_t latest_measured_avg_occ = 0;
uint32_t latest_measured_avg_pcie_bw = 0;
uint32_t smoothed_avg_pcie_bw_lt = 0;
uint32_t smoothed_avg_pcie_bw = 0;
float smoothed_avg_pcie_bw_f_lt = (float) PCIE_BW_THRESHOLD;
float smoothed_avg_pcie_bw_f = (float) PCIE_BW_THRESHOLD;
uint32_t latest_n_measured_avg_occ[THRESH_NUM_SAMPLES];
float latest_measured_avg_occ_thresh_avg = 0;
uint64_t latest_mba_update_tsc = 0;

uint64_t cur_cum_frc = 0;
uint64_t prev_cum_frc = 0;
uint64_t cum_frc_sample = 0;

uint32_t app_pid = 0;

uint64_t last_reduced_tsc = 0;
// uint32_t reduction_timeout = 200;
uint32_t reduction_timeout = 150;
#define MBA_DECREASE_TIMEOUT 200 //time in us needed before any two reduction calls to mba
#define MIN_REDUCTION_TIMEOUT 100
#define MAX_REDUCTION_TIMEOUT 5000

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

void rdmsr_userspace(int core, uint64_t rd_msr, uint64_t *rd_val_addr){
    rc64 = pread(msr_fd[core],rd_val_addr,sizeof(rd_val_addr),rd_msr);
    if (rc64 != sizeof(rd_val_addr)) {
        fprintf(log_file,"ERROR: failed to read MSR %x on Logical Processor %d", rd_msr, core);
        exit(-1);
    }
}

void wrmsr_userspace(int core, uint64_t wr_msr, uint64_t *wr_val_addr){
    rc64 = pwrite(msr_fd[core],wr_val_addr,sizeof(wr_val_addr),wr_msr);
    if (rc64 != 8) {
        fprintf(log_file,"ERROR writing to MSR device on core %d, write %ld bytes\n",core,rc64);
        exit(-1);
    }
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
	LOG[log_index % LOG_SIZE].l_avg_rd_bw = latest_avg_rd_bw;
	LOG[log_index % LOG_SIZE].l_avg_wr_bw = latest_avg_wr_bw;
	LOG[log_index % LOG_SIZE].cpu = c;
	LOG[log_index % LOG_SIZE].l_mba_val = latest_mba_val;
	LOG[log_index % LOG_SIZE].l_measured_avg_occ = latest_measured_avg_occ;
	LOG[log_index % LOG_SIZE].l_measured_avg_pcie_bw = smoothed_avg_pcie_bw;
	LOG[log_index % LOG_SIZE].l_measured_lat_pcie_bw = latest_measured_avg_pcie_bw;
	LOG[log_index % LOG_SIZE].l_measured_avg_occ_thresh_avg = latest_measured_avg_occ_thresh_avg;
	LOG[log_index % LOG_SIZE].l_red_timeout = reduction_timeout;
	log_index++;
}

static void update_imc_config(void){
	//program the desired BDF values to measure IMC counters
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
	while (i<200) {
		rc = fscanf(input_file,"%d %d %d %d %x %s",&socket,&imc,&subchannel,&counter,&value,&description);
		if (rc == EOF) break;
		i++;
		#if DEBUG_MODE
		fprintf(log_file,"DEBUG: Uncore IMC PerfEvtSel input file contains %d %d %d %d 0x%x %s\n",socket,imc,subchannel,counter,value,description);
		#endif
		channel = 3*imc + subchannel;				// PCI device/function is indexed by channel here (0-5)
		bus = IMC_BUS_Socket[socket];
		device = IMC_Device_Channel[channel];
		function = IMC_Function_Channel[channel];
		offset = IMC_PmonCtl_Offset[counter];
		// fprintf(log_file,"DEBUG: translated bus/device/function/offset values %#x %#x %#x %#x\n",bus,device,function,offset);
		index = PCI_cfg_index(bus, device, function, offset);
		mmconfig_ptr[index] = value;
		// strncpy(imc_event_name[socket][channel][counter],description,32);
	}
}

static void sample_imc_counters(){
    int bus, device, function, offset, imc, channel, subchannel, counter;
    uint32_t index, low, high;
    uint64_t count;

    //first sample IMC counters
    bus = IMC_BUS_Socket[SOCKET];
    for (channel=0; channel<NUM_IMC_CHANNELS; channel++) {
        device = IMC_Device_Channel[channel];
        function = IMC_Function_Channel[channel];
        for (counter=0; counter<NUM_IMC_COUNTERS; counter++) {
            offset = IMC_PmonCtr_Offset[counter];
            index = PCI_cfg_index(bus, device, function, offset);
            low = mmconfig_ptr[index];
            high = mmconfig_ptr[index+1];
            count = ((uint64_t) high) << 32 | (uint64_t) low;
            imc_counts[channel][counter] = count;
            prev_imc_counts[channel][counter] = cur_imc_counts[channel][counter];
            cur_imc_counts[channel][counter] = count;
        }
    }
}

static void sample_iio_free_running_counter(int c){
    uint64_t rd_val = 0;
	msr_num = IIO_PCIE_1_PORT_0_BW_IN;
	rdmsr_userspace(c,msr_num,&rd_val);
	cum_frc_sample = rd_val;
	prev_cum_frc = cur_cum_frc;
	cur_cum_frc = cum_frc_sample;
}

static void sample_time_counter(){
    tsc_sample = rdtscp();
	prev_rdtsc = cur_rdtsc;
	cur_rdtsc = tsc_sample;
}

static void sample_counters(int c){
    //sample the memory bandwidth
    sample_imc_counters();

    //sample pcie bandwidth
    sample_iio_free_running_counter(c);

	//sample time at the last
	sample_time_counter();
	return;
}

static void update_imc_bw(void){
	// latest_time_delta_us = (cur_rdtsc - prev_rdtsc) / 3300;
    int channel;
	latest_time_delta_ns = ((cur_rdtsc - prev_rdtsc) * 10) / 33;
	if(latest_time_delta_ns > 0){
        latest_avg_rd_bw = 0;
        latest_avg_wr_bw = 0;
        for(channel=0;channel<NUM_IMC_CHANNELS;channel++){
            latest_avg_rd_bw += (cur_imc_counts[channel][0] - prev_imc_counts[channel][0]) * 64 / (latest_time_delta_ns);
            latest_avg_wr_bw += (cur_imc_counts[channel][1] - prev_imc_counts[channel][1]) * 64 / (latest_time_delta_ns);
        }
	}
	// float(log[i] - log[i-1])*cacheline / (float(times[i] - times[i-1]) * 1e-6);
}

static void update_pcie_bw(void){
    latest_time_delta_ns = ((cur_rdtsc - prev_rdtsc) * 10) / 33;
	if(latest_time_delta_ns > 0){
		latest_measured_avg_pcie_bw = (uint32_t)((((float)(cur_cum_frc - prev_cum_frc)) / ((float)(latest_time_delta_ns)) ) * 32);
        if(latest_measured_avg_pcie_bw < 150){
            smoothed_avg_pcie_bw_f_lt = ((1023.0*smoothed_avg_pcie_bw_f_lt) + latest_measured_avg_pcie_bw) / 1024.0;
            smoothed_avg_pcie_bw_f = ((127.0*smoothed_avg_pcie_bw_f) + latest_measured_avg_pcie_bw) / 128.0;
            // smoothed_avg_pcie_bw_f = latest_measured_avg_pcie_bw;
            smoothed_avg_pcie_bw_lt = (uint32_t) smoothed_avg_pcie_bw_f_lt;
            smoothed_avg_pcie_bw = (uint32_t) smoothed_avg_pcie_bw_f;
            // smoothed_avg_occ = ((7*smoothed_avg_occ) + latest_avg_occ) >> 3;
        }
	}
}

static void update_reduction_timeout(void){
    // if(smoothed_avg_pcie_bw_lt > PCIE_BW_THRESHOLD + BW_TOLERANCE){
    //     if(reduction_timeout > MIN_REDUCTION_TIMEOUT){
    //         assert(MIN_REDUCTION_TIMEOUT > 50);
    //         reduction_timeout = reduction_timeout - 50;
    //     }
    // }
    // if(smoothed_avg_pcie_bw_lt < PCIE_BW_THRESHOLD - BW_TOLERANCE){
    //     if(reduction_timeout < MAX_REDUCTION_TIMEOUT){
    //         reduction_timeout = reduction_timeout + 50;
    //     }
    // }
}

static void update_mba_msr_register(void){
    msr_num = PQOS_MSR_MBA_MASK_START + MBA_COS_ID;
    uint64_t wr_val = 0;
    wrmsr_userspace(NUMA1_CORE,msr_num,&wr_val);
    wrmsr_userspace(NUMA2_CORE,msr_num,&wr_val);
    wrmsr_userspace(NUMA3_CORE,msr_num,&wr_val);
}

static void update_mba_process_scheduler(void){
    // assert(latest_mba_val >= 0);
    assert(latest_mba_val <= 4);
    // if(app_pid != 0){
        if(latest_mba_val == 4){
            kill(app_pid,SIGSTOP);
        }
        else{
            kill(app_pid,SIGCONT);
        }
    // }
}

static void increase_mba_val(void){
    msr_num = PQOS_MSR_MBA_MASK_START + MBA_COS_ID;
    uint64_t wr_val = MBA_VAL_HIGH;

    assert(latest_mba_val >= 0);
    #if !(USE_PROCESS_SCHEDULER)
    assert(latest_mba_val <= 3);
    #endif
    #if USE_PROCESS_SCHEDULER
    assert(latest_mba_val <= 4); //level 4 means infinite latency by MBA -- essentially SIGSTOP
    #endif

    if(latest_mba_val < 3){
        latest_mba_val++;
        switch(latest_mba_val){
            case 0:
                assert(false);
                break;
            case 1:
                wrmsr_userspace(NUMA1_CORE,msr_num,&wr_val);
                break;
            case 2:
                wrmsr_userspace(NUMA2_CORE,msr_num,&wr_val);
                break;
            case 3:
                wrmsr_userspace(NUMA3_CORE,msr_num,&wr_val);
                break;
            default:
                assert(false);
                break;
        }
    }
    #if USE_PROCESS_SCHEDULER
    else if(latest_mba_val == 3){
        latest_mba_val++;
        update_mba_process_scheduler(); //should initiate SIGSTOP
    }
    #endif
}

static void decrease_mba_val(void){
    uint64_t cur_tsc_val = rdtscp();
    if((cur_tsc_val - last_reduced_tsc) / 3300 < reduction_timeout){
        return;
    }
    msr_num = PQOS_MSR_MBA_MASK_START + MBA_COS_ID;
    uint64_t wr_val = MBA_VAL_LOW;

    assert(latest_mba_val >= 0);
    #if !(USE_PROCESS_SCHEDULER)
    assert(latest_mba_val <= 3);
    #endif
    #if USE_PROCESS_SCHEDULER
    assert(latest_mba_val <= 4);
    #endif

    update_reduction_timeout();

    if(latest_mba_val > 0){
        latest_mba_val--;
        switch(latest_mba_val){
            case 0:
                wrmsr_userspace(NUMA1_CORE,msr_num,&wr_val);
                last_reduced_tsc = rdtscp();
                break;
            case 1:
                wrmsr_userspace(NUMA2_CORE,msr_num,&wr_val);
                last_reduced_tsc = rdtscp();
                break;
            case 2:
                wrmsr_userspace(NUMA3_CORE,msr_num,&wr_val);
                last_reduced_tsc = rdtscp();
                break;
            case 3:
                #if !(USE_PROCESS_SCHEDULER)
                assert(false);
                #endif
                #if USE_PROCESS_SCHEDULER
                update_mba_process_scheduler();
                last_reduced_tsc = rdtscp();
                #endif
                break;
            default:
                assert(false);
                break;
        }
    }
}

static void update_mba_val(void){

    #if !(MBA_TEST)
    
    if(smoothed_avg_pcie_bw < (PCIE_BW_THRESHOLD - BW_TOLERANCE)){
        if(latest_measured_avg_occ > IIO_THRESHOLD){
            increase_mba_val();
        }
    }

    // if(smoothed_avg_pcie_bw_lt > (PCIE_BW_THRESHOLD + BW_TOLERANCE)){
    if(smoothed_avg_pcie_bw > (PCIE_BW_THRESHOLD + BW_TOLERANCE)){
        if(latest_measured_avg_occ < IIO_THRESHOLD){
            decrease_mba_val();
        }
    }
    #endif
}

void main_init() {
    //initialize the log
    int i=0;
    while(i<LOG_SIZE){
        LOG[i].l_tsc = 0;
        LOG[i].td_ns = 0;
        LOG[i].l_avg_rd_bw = 0;
        LOG[i].l_avg_wr_bw = 0;
        LOG[i].cpu = 65;
        LOG[i].l_mba_val = 0;
        LOG[i].l_measured_avg_occ = 0;
        LOG[i].l_measured_avg_pcie_bw = 0;
        LOG[i].l_measured_lat_pcie_bw = 0;
        LOG[i].l_measured_avg_occ_thresh_avg = 0;
        LOG[i].l_red_timeout = 0;
        i++;
    }
    for(i=0;i<THRESH_NUM_SAMPLES;i++){
        latest_n_measured_avg_occ[i] = 0;
    }
    update_imc_config();
}

void main_exit() {
    //dump log info
    int i=0;
    fprintf(log_file,"index,latest_tsc,time_delta_ns,avg_rd_bw,avg_wr_bw,cpu,latest_mba_val,latest_measured_avg_occ,latest_measured_avg_occ_thresh_avg,smooth_pcie_bw,latest_pcie_bw,reduction_timeout\n");
    while(i<LOG_SIZE){
        fprintf(log_file,"%d,%lld,%lld,%f,%f,%d,%d,%d,%f,%d,%d,%d\n",
        i,
        LOG[i].l_tsc,
        LOG[i].td_ns,
        LOG[i].l_avg_rd_bw,
        LOG[i].l_avg_wr_bw,
        LOG[i].cpu,
        LOG[i].l_mba_val,
        LOG[i].l_measured_avg_occ,
        LOG[i].l_measured_avg_occ_thresh_avg,
        LOG[i].l_measured_avg_pcie_bw,
        LOG[i].l_measured_lat_pcie_bw,
        LOG[i].l_red_timeout);
        i++;
    }

    if(latest_mba_val > 0){
        latest_mba_val = 0;
        update_mba_msr_register();
        // #if !(USE_PROCESS_SCHEDULER)
        // update_mba_msr_register();
        // #endif
        #if USE_PROCESS_SCHEDULER
        update_mba_process_scheduler();
        #endif
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

    char filename[100];
    sprintf(filename,"log.mba");
    log_file = fopen(filename,"w+");
    if (log_file == 0) {
        fprintf(stderr,"ERROR %s when trying to open log file %s\n",strerror(errno),filename);
        exit(-1);
    }

    int nr_cpus = NUM_LPROCS;
    int i;
    for (i=0; i<nr_cpus; i++) {
		sprintf(filename,"/dev/cpu/%d/msr",i);
		msr_fd[i] = open(filename, O_RDWR);
		// printf("   open command returns %d\n",msr_fd[i]);
		if (msr_fd[i] == -1) {
			fprintf(log_file,"ERROR %s when trying to open %s\n",strerror(errno),filename);
			exit(-1);
		}
	}

    #if USE_PROCESS_SCHEDULER
    char line[32];
    FILE *cmd = popen("pidof mlc", "r");

    fgets(line, 32, cmd);
    uint32_t pid = strtoul(line, NULL, 10);
    app_pid = pid;
    printf("MLC PID: %ld",app_pid);

    pclose(cmd);
    #endif

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


    #if SH_MEM
    // ftok to generate unique key
    key_t key = ftok("shmfile",65);
  
    // shmget returns an identifier in shmid
    int shmid = shmget(key,5,0666|IPC_CREAT);
  
    // shmat to attach to shared memory
    char *str = (char*) shmat(shmid,(void*)0,0);
    #endif

    int cpu = get_core_number();
    // fprintf(log_file,"Core no: %d\n",cpu);

    main_init();
    
    while(1){
        sample_counters(cpu);
        update_imc_bw();
        update_pcie_bw();
        // update_reduction_timeout();
        // update_mba_val();
        update_log(cpu);
        counter++;
        #if SH_MEM
        char * pEnd = NULL;
        long sh_mem_num = 0;
        sh_mem_num = strtol(str,str+5,10);
        // printf("%s : %ld\n",str,sh_mem_num);
        latest_measured_avg_occ = sh_mem_num;
        int i = 0;
        latest_measured_avg_occ_thresh_avg = 0;
        for(i=0;i<THRESH_NUM_SAMPLES-1;i++){
            latest_n_measured_avg_occ[i] = latest_n_measured_avg_occ[i+1];
            latest_measured_avg_occ_thresh_avg += latest_n_measured_avg_occ[i];
        }
        latest_n_measured_avg_occ[THRESH_NUM_SAMPLES-1] = latest_measured_avg_occ;
        latest_measured_avg_occ_thresh_avg += latest_n_measured_avg_occ[THRESH_NUM_SAMPLES-1];
        latest_measured_avg_occ_thresh_avg /= (THRESH_NUM_SAMPLES);
        #endif
    }

    #if SH_MEM
    //detach from shared memory 
    shmdt(str);
    
    // // destroy the shared memory
    // shmctl(shmid,IPC_RMID,NULL);
    #endif

    main_exit();
    return 0;
}