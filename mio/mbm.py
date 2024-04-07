# Intel MBM runner
import subprocess
import os

class MBMRunner:
    def __init__(self, pqos_path):
        self.pqos_path = os.path.join(pqos_path, 'pqos')

        self.proc = None

    # Run for a given duration (blocking call)
    def run(self, out_path, cores, duration):
        out_f = open(out_path, 'w')
        args = [self.pqos_path, '-m']
        cores_str = ','.join([str(x) for x in cores])
        args.append('mbl:%s;mbr:%s'%(cores_str, cores_str))
        args.append('-u')
        args.append('csv')
        args.append('-t')
        args.append(str(duration))
        args.append('-i')
        args.append('10')

        self.proc = subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT)
        self.proc.wait()

    def cleanup(self):
        if self.proc:
            self.proc.kill()
    

