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

        # Get cpu topology
        # TODO: Make this generic
        self.numa_cores = [[3,7,11,15,19,23,27,31], [0,4,8,12,16,20,24,28], [1,5,9,13,17,21,25,29], [2,6,10,14,18,22,26,30]]

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
