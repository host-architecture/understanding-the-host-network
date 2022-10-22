import subprocess
import os

class SarRunner:
    def __init__(self):
        self.proc = None

    # Run for a given duration (blocking call)
    def run(self, out_path, duration):
        out_f = open(out_path, 'w')
        args = ['sar', '-u', '1', str(duration), '-P', 'ALL']
        self.proc = subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT)
        self.proc.wait()

    def cleanup(self):
        if self.proc:
            self.proc.kill()