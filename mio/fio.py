import subprocess, os, signal


class FIORunner:
    def __init__(self, path):
        self.fio_path = os.path.join(path, 'fio')

    def init(self, output_path, cores, mem_numa, io_size, io_depth, write_frac, disk):
        self.output_path = output_path
        self.cores = cores
        self.mem_numa = mem_numa

        # Default parameters
        self.io_size = io_size
        self.io_depth = io_depth
        self.write_frac = write_frac
        self.disk = disk
        self.rate_cap = None

        self.proc = None

    def run(self, duration):
        out_f = open(self.output_path, 'w')
        # numactl --membind 3 ./fio --filename=/dev/nvme0n1 --name=test  --ioengine=libaio  --direct=1  --rw=randread  --gtod_reduce=0  --cpus_allowed_policy=split  --time_based  --size=1G  --runtime=10  --cpus_allowed=3,7  --numjobs=2  --bs=$((4*1024))  --iodepth=64 --group_reporting
        cores_str = ','.join([str(x) for x in self.cores])
        args = ['numactl', '--membind', str(self.mem_numa), self.fio_path, '--name=test', '--ioengine=libaio', '--direct=1', '--gtod_reduce=0', '--cpus_allowed_policy=split', '--time_based', '--size=1G', '--runtime=%d'%(duration), '--cpus_allowed=%s'%(cores_str), '--numjobs=1', '--group_reporting', '--scramble_buffers=0']
        args.append('--filename=%s'%(self.disk))
        args.append('--bs=%d'%(self.io_size))
        args.append('--iodepth=%d'%(self.io_depth))
        
        if self.write_frac == 0:
            args.append('--rw=randread')
        elif self.write_frac == 100:
            args.append('--rw=randwrite')

        if self.rate_cap:
            args.append('--rate_iops=%d'%(self.rate_cap))
        
        self.proc = subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT)

    def end(self):
        os.kill(self.proc.pid, signal.SIGINT)

    def set_ratecap(self, val):
        self.rate_cap = val

    def wait(self):
        if self.proc:
            self.proc.wait()

    def cleanup(self):
        if self.proc:
            self.proc.kill()