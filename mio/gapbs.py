from .antagonist import *

import subprocess, os, time, signal

class GAPBSRunner(Antagonist):
    def __init__(self, path, workload):
        self.gapbs_path = os.path.join(path, workload)

    def init(self, output_path, cores, mem_numa, opts):
        self.output_path = output_path
        self.cores = cores
        self.mem_numa = mem_numa
        self.opts = opts

        # Default parameters
        self.graph_size = 25 # 2^25 nodes
        self.iterations0 = 3
        self.iterations = min(len(self.cores), 16)*self.iterations0

        # numactl --membind 3 --physcpubind 11,15,19,23,27 ./pr -u 25 -n 16
        out_f = open(self.output_path, 'w')
        self.proc = subprocess.Popen(['numactl', '--membind', str(self.mem_numa), '--physcpubind', ','.join([str(x) for x in self.cores]), self.gapbs_path, '-u', str(self.graph_size), '-n', str(self.iterations)], stdout=out_f, stderr=subprocess.STDOUT)

        # Wait for graph to be initialized
        while True:
            if self.proc.poll():
                # Process has already exited (likely due to error)
                raise Exception('GAPBS process exited before initilization hook')
            read_f = open(self.output_path, 'r')
            done = False
            for line in read_f:
                if 'Graph has' in line:
                    os.kill(self.proc.pid, signal.SIGSTOP)
                    done = True
            if done:
                break
            time.sleep(1)

        print('Initilized GAPBS')

    def run(self, duration):
        # Duration is ignored

        # Simply resume the process
        os.kill(self.proc.pid, signal.SIGCONT)

    def wait(self):
        self.proc.wait()

    def cleanup(self):
        self.proc.kill()

    def set_instsize(self, size):
        raise Exception('Not supported')

    def set_pattern(self, pattern):
        raise Exception('Not supported')
    
    def set_hugepages(self, val):
        raise Exception('Not supported')
    
    def set_writefrac(self, val):
        raise Exception('Not supported')
