from .antagonist import *

import subprocess, os

class MLCRunner(Antagonist):
    def __init__(self, path):
        self.mlc_path = os.path.join(path, 'mlc')

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

        self.proc = None

    def run(self, duration):
        out_f = open(self.output_path, 'w')
        # $MLC_PATH/mlc --loaded_latency -T -d0 -e -k$cores_str -j0 -b1g -t$duration $workload $avx512flag
        cores_str = ','.join([str(x) for x in self.cores])
        args = [self.mlc_path, '--loaded_latency', '-T', '-d0', '-e', '-k' + cores_str, '-j' + str(self.mem_numa), '-b1g', '-t' + str(duration)]
        
        if self.write_frac == 0:
            args.append('-R')
        elif self.write_frac == 50:
            args.append('-W5')
        elif self.write_frac == 100:
            args.append('-W6')
        elif self.write_frac == 66:
            args.append('-W2')

        if self.instsize == 32:
            args.append('-Y')
        elif self.instsize == 64:
            args.append('-Z')

        if self.pattern == 'random':
            args.append('-U')
        
        self.proc = subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT)

    def wait(self):
        if self.proc:
            self.proc.wait()

    def cleanup(self):
        if self.proc:
            self.proc.kill()

    def set_instsize(self, size):
        if size not in [16, 32, 64]:
            raise Exception('Instruction size not supported')
        self.instsize = size

    def set_pattern(self, pattern):
        if pattern not in ['sequential', 'random']:
            raise Exception('Pattern not supported')
        self.pattern = pattern
    
    def set_hugepages(self, val):
        self.hugepages = val
    
    def set_writefrac(self, val):
        if not val in [0, 50, 66, 100]:
            raise Exception('Write fraction not supported')

        self.write_frac = val
