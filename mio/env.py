from distutils.command.config import config
import json
import os

class Environment:
    def __init__(self, configpath):
        with open(configpath, 'r') as f:
            config_dict = json.load(f)

        self.mlc_path = None
        self.pcm_path = None
        self.stats_path = None
        self.fio_path = None
        self.stream_path = None
        self.redis_path = None
        self.memtier_path = None
        self.mmapbench_path = None
        self.gapbs_path = None
        self.ssds = None
        self.mem_channels = None

        if 'MLC_PATH' in config_dict:
            self.mlc_path = config_dict['MLC_PATH']

        if 'PCM_PATH' in config_dict:
            self.pcm_path = config_dict['PCM_PATH']

        if 'STATS_PATH' in config_dict:
            self.stats_path = config_dict['STATS_PATH']

        if 'FIO_PATH' in config_dict:
            self.fio_path = config_dict['FIO_PATH']

        if 'STREAM_PATH' in config_dict:
            self.stream_path = config_dict['STREAM_PATH']
        
        if 'MMAPBENCH_PATH' in config_dict:
            self.mmapbench_path = config_dict['MMAPBENCH_PATH']

        if 'REDIS_PATH' in config_dict:
            self.redis_path = config_dict['REDIS_PATH']

        if 'MEMTIER_PATH' in config_dict:
            self.memtier_path = config_dict['MEMTIER_PATH']

        if 'GAPBS_PATH' in config_dict:
            self.gapbs_path = config_dict['GAPBS_PATH']

        # Get cpu topology
        # TODO: Make this generic
        if 'NUMA_CORES' not in config_dict:
            raise Exception('NUMA_CORES not defined in config')
        self.numa_cores = [[int(z) for z in y.split(',')] for y in config_dict['NUMA_CORES']]
        # self.numa_cores = [[0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,66,68,70,72,74,76,78,80,82,84,86,88,90,92,94,96,98,100,102,104,106,108,110,112,114,116,118,120,122,124,126], [1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49,51,53,55,57,59,61,63,65,67,69,71,73,75,77,79,81,83,85,87,89,91,93,95,97,99,101,103,105,107,109,111,113,115,117,119,121,123,125,127]]

        # Default numa order
        if 'NUMA_ORDER' not in config_dict:
            raise Exception('NUMA_ORDER not defined in config')
        self.numa_order = [int(x) for x in config_dict['NUMA_ORDER'].split(',')]
        if len(self.numa_order) > len(self.numa_cores):
            raise Exception('config error: Length of NUMA_ORDER exceeds number of NUMA nodes')

        if 'SSDS' in config_dict:
            self.ssds = config_dict['SSDS']

        if 'MEM_CHANNELS' in config_dict:
            self.mem_channels = config_dict['MEM_CHANNELS']

        if 'CHAS' in config_dict:
            self.chas = config_dict['CHAS']

        if 'IRPS' in config_dict:
            self.irps = config_dict['IRPS']

        if 'CHA_FREQ' in config_dict:
            self.cha_freq = config_dict['CHA_FREQ']

        if 'IMC_FREQ' in config_dict:
            self.imc_freq = config_dict['IMC_FREQ']


        if os.system('modprobe msr') != 0:
            raise Exception('Failed to load msr kernel module')


    def get_mlc_path(self):
        if not self.mlc_path:
            raise Exception('MLC Path not specified')
        return self.mlc_path

    def get_pcm_path(self):
        if not self.pcm_path:
            raise Exception('PCM Path not specified')
        return self.pcm_path

    def get_stats_path(self):
        if not self.stats_path:
            raise Exception('Stats Path not specified')
        return self.stats_path

    def get_fio_path(self):
        if not self.fio_path:
            raise Exception('FIO Path not specified')
        return self.fio_path

    def get_stream_path(self):
        if not self.stream_path:
            raise Exception('STREAM Path not specified')
        return self.stream_path

    def get_redis_path(self):
        if not self.redis_path:
            raise Exception('Redis Path not specified')
        return self.redis_path

    def get_memtier_path(self):
        if not self.memtier_path:
            raise Exception('Memtier Path not specified')
        return self.memtier_path

    def get_mmapbench_path(self):
        if not self.mmapbench_path:
            raise Exception('MMAPBENCH_PATH not specified')
        return self.mmapbench_path

    def get_gapbs_path(self):
        if not self.gapbs_path:
            raise Exception('GAPBS_PATH not specificed')
        return self.gapbs_path

    def enable_prefetch(self):
        if os.system('wrmsr -a 0x1a4 0') != 0:
            raise Exception('Enable prefetch failed')

    def disable_prefetch(self):
        if os.system('wrmsr -a 0x1a4 15') != 0:
            raise Exception('Disable prefetch failed')
    
    def disable_prefetch_l1(self):
        if os.system('wrmsr -a 0x1a4 12') != 0:
            raise Exception('Disable L1 prefetch failed')

    def enable_hugepages(self):
        for i in range(self.get_num_numa()):
            ret = os.system('echo 64 > /sys/devices/system/node/node%d/hugepages/hugepages-1048576kB/nr_hugepages' % (i))
            if ret != 0:
                raise Exception('Failed to allocate hugepages on NUMA node %d' % (i))

    def disable_hugepages(self):
        for i in range(self.get_num_numa()):
            ret = os.system('echo 0 > /sys/devices/system/node/node%d/hugepages/hugepages-1048576kB/nr_hugepages' % (i))
            if ret != 0:
                raise Exception('Failed to deallocate hugepages on NUMA node %d' % (i))

    def get_num_numa(self):
        return len(self.numa_cores)

    def get_cores_in_numa(self, i):
        return self.numa_cores[i]

    def get_numa_order(self):
        return self.numa_order

    def get_ssds(self):
        if not self.ssds:
            raise Exception('SSDS config not found')
        return self.ssds

    def get_mem_channels(self):
        if not self.mem_channels:
            raise Exception('MEM_CHANNELS config not found')
        return self.mem_channels
    
    def get_chas(self):
        if not self.chas:
            raise Exception('CHAS config not found')
        return self.chas

    def get_irps(self):
        if not self.irps:
            raise Exception('IRPS config not found')
        return self.irps
    
    def get_cha_freq(self):
        if not self.cha_freq:
            raise Exception('CHA_FREQ config not found')
        return self.cha_freq
    
    def get_imc_freq(self):
        if not self.imc_freq:
            raise Exception('IMC_FREQ config not found')
        return self.imc_freq
    