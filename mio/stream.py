from .antagonist import *

import subprocess, os
import threading, time
import signal

class STREAMRunner(Antagonist):
    def __init__(self, path):
        self.stream_path = os.path.join(path, 'stream')

    def init(self, output_path, cores, mem_numa, opts):
        self.output_path = output_path
        self.cores = cores
        if 'mem_numa_list' in opts:
            self.mem_numa = opts['mem_numa_list']
        else:
            self.mem_numa = [mem_numa for _ in range(len(cores))]
        
        # Vary number of cores over time
        # 'vary_load' is a list if integers specifying specifying the number of active cores every second
        if 'vary_load' in opts:
            self.vary_load = opts['vary_load']
        else:
            self.vary_load = []

        self.opts = opts

        # Default parameters
        self.instsize = 16
        self.pattern = 'sequential'
        self.hugepages = False
        self.write_frac = 0

        self.procs = []
        self.vary_load_thread = None

    def run(self, duration):
        idx = 0
        for i in self.cores:
            out_f = open(self.output_path + ('-core%d'%(i)), 'w')
        # numactl --membind 3 --physcpubind 3 ./stream Read16 10
            args = []
            args += ['numactl', '--membind', str(self.mem_numa[idx]), '--physcpubind', str(i), self.stream_path]
        
            workload_str = ''
            if self.write_frac == 0:
                workload_str += 'Read'
            elif self.write_frac == 50:
                workload_str += 'ReadWrite'
            elif self.write_frac == 100:
                workload_str += 'NtWrite'

            if self.instsize == 16:
                workload_str += '16'
            elif self.instsize == 64:
                workload_str += '64'

            if self.pattern == 'random':
                workload_str += 'Random'

            if self.pattern == 'random' and 'chunk_size' in self.opts:
                workload_str += ('Chunk' + str(self.opts['chunk_size']))
            
            # TODO: Clean up
            if self.pattern == 'triad':
                workload_str = 'Triad'

            args.append(workload_str)
            args.append(str(duration))

            my_env = os.environ.copy()

            if self.hugepages:
                my_env['STREAM_HUGEPAGES'] = 'on'

            if 'warmup_duration' in self.opts:
                my_env['WARMUP_DURATION'] = str(self.opts['warmup_duration'])

            if 'cooldown_duration' in self.opts:
                my_env['COOLDOWN_DURATION'] = str(self.opts['cooldown_duration'])

            self.procs.append(subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT, env=my_env))
            idx += 1
        
        if len(self.vary_load) > 0:
            # sanity check
            if(max(self.vary_load) > len(self.cores)):
                raise Exception('vary_load contains value greater than max cores provisisoned')
            self.vary_load_thread = threading.Thread(target=self.vary_load_worker)
            self.vary_load_stop = threading.Event()
            self.vary_load_thread.start()

    def vary_load_worker(self):
        # Warmup duration before varying load
        time.sleep(5)
        # Pause all cores
        for p in self.procs:
            p.send_signal(signal.SIGSTOP)

        cur_active_cores = 0
        for active_cores in self.vary_load:
            time.sleep(1)
            if(active_cores > cur_active_cores):
                for i in range(cur_active_cores, active_cores):
                    self.procs[i].send_signal(signal.SIGCONT)
            elif(active_cores < cur_active_cores):
                for i in range(active_cores, cur_active_cores):
                    self.procs[i].send_signal(signal.SIGSTOP)
            cur_active_cores = active_cores

    def wait(self):
        if self.vary_load_thread:
            self.vary_load_thread.join()
        for p in self.procs:
            p.wait()

    def cleanup(self):
        if self.vary_load_thread:
            self.vary_load_stop.set()
            self.vary_load_thread.join()
        for p in self.procs:
            p.kill()

    def set_instsize(self, size):
        if size not in [16, 64]:
            raise Exception('Instruction size not supported')
        self.instsize = size

    def set_pattern(self, pattern):
        if pattern not in ['sequential', 'random', 'triad']:
            raise Exception('Pattern not supported')
        self.pattern = pattern
    
    def set_hugepages(self, val):
        self.hugepages = val
    
    def set_writefrac(self, val):
        if not val in [0, 50, 100]:
            raise Exception('Write fraction not supported')

        self.write_frac = val
