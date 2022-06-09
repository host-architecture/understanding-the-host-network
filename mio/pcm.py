import subprocess
import os

class PcmRawRunner:
    def __init__(self, pcm_path):
        self.pcm_raw_path = os.path.join(pcm_path, 'pcm-raw.x')

        self.proc = None

    # Run for a given duration (blocking call)
    def run(self, out_path, events, duration):
        out_f = open(out_path, 'w')
        args = [self.pcm_raw_path, '1.0']
        for evt in events:
            args.append('-e')
            args.append(events[evt] + ',' + 'name=' + evt)
        args.append('-f')

        self.proc = subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT)
        try:
            self.proc.wait(timeout=duration)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc = None

    def cleanup(self):
        if self.proc:
            self.proc.kill()


class PcmMemoryRunner:
    def __init__(self, pcm_path):
        self.pcm_memory_path = os.path.join(pcm_path, 'pcm-memory.x')

        self.proc = None

    # Run for a given duration (blocking call)
    def run(self, out_path, duration):
        out_f = open(out_path, 'w')
        args = [self.pcm_memory_path, '-csv']

        self.proc = subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT)
        try:
            self.proc.wait(timeout=duration)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc = None

    def cleanup(self):
        if self.proc:
            self.proc.kill()
            
            
class PcmLatencyRunner:
    def __init__(self, pcm_path):
        self.pcm_memory_path = os.path.join(pcm_path, 'pcm-latency.x')

        self.proc = None

    # Run for a given duration (blocking call)
    def run(self, out_path, duration):
        out_f = open(out_path, 'w')
        args = [self.pcm_memory_path]

        self.proc = subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT)
        try:
            self.proc.wait(timeout=duration)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            self.proc = None

    def cleanup(self):
        if self.proc:
            self.proc.kill()

    

