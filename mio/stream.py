from .antagonist import *

import subprocess, os

class STREAMRunner(Antagonist):
    def __init__(self, path):
        self.stream_path = os.path.join(path, 'stream')

    def init(self, output_path, cores, mem_numa, opts):
        self.output_path = output_path
        self.cores = cores
        self.mem_numa = mem_numa
        self.opts = opts

        # Default parameters
        self.instsize = 16
        self.pattern = 'sequential'
        self.hugepages = False
        self.write_frac = 0

        self.procs = []

    def run(self, duration):
        for i in self.cores:
            out_f = open(self.output_path + ('core%d'%(i)), 'w')
        # numactl --membind 3 --physcpubind 3 ./stream Read16 10
            args = ['numactl', '--membind', str(self.mem_numa), '--physcpubind', str(i), self.stream_path]
        
            workload_str = ''
            if self.write_frac == 0:
                workload_str += 'Read'
            elif self.write_frac == 50:
                workload_str += 'ReadWrite'

            if self.instsize == 16:
                workload_str += '16'

            # if self.pattern == 'random':
            #     args.append('-U')

            args.append(workload_str)
            args.append(str(duration))
            
            self.procs.append(subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT))

    def wait(self):
        for p in self.procs:
            p.wait()

    def cleanup(self):
        for p in self.procs:
            p.kill()

    def set_instsize(self, size):
        if size not in [16]:
            raise Exception('Instruction size not supported')
        self.instsize = size

    def set_pattern(self, pattern):
        if pattern not in ['sequential']:
            raise Exception('Pattern not supported')
        self.pattern = pattern
    
    def set_hugepages(self, val):
        self.hugepages = val
    
    def set_writefrac(self, val):
        if not val in [0, 50]:
            raise Exception('Write fraction not supported')

        self.write_frac = val