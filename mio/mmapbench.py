import subprocess, os

class MmapBenchRunner:
    def __init__(self, path):
        self.mmapbench_path = os.path.join(path, 'mmapbench')

    def init(self, output_path, cores, mem_numa, threads_per_core, ssds, area_size, pgcache_frac, opts):
        self.output_path = output_path
        self.cores = cores
        self.mem_numa = mem_numa
        self.opts = opts
        self.threads_per_core = threads_per_core
        self.ssds = ssds
        self.area_size = area_size
        self.pgcache_frac = pgcache_frac
        self.cg_per_process = False
        if 'cg_per_process' in opts:
            self.cg_per_process = True

        # Default parameters
        self.instsize = 64
        self.pattern = 'sequential'
        self.hugepages = False
        self.write_frac = 0

        self.procs = []

        # Create cgroup for page cache memory limit
        # Shouldn't fail if already present
        if not self.cg_per_process:
            pgcache_limit = int(self.pgcache_frac * self.area_size * len(self.cores) * self.threads_per_core) 
            ret = os.system('cgcreate -g memory:/mmapbench')
            if ret != 0:
                raise Exception('cgroup creation failed')
            ret = os.system('echo %d > /sys/fs/cgroup/memory/mmapbench/memory.limit_in_bytes'%(pgcache_limit))
            if ret != 0:
                raise Exception('Setting cgroup memory limit failed')
        else:
            # Create per-process cgroups
            pgcache_limit = int(self.pgcache_frac * self.area_size)
            num_procs = self.threads_per_core * len(self.cores)
            for i in range(num_procs):
                ret = os.system('cgcreate -g memory:/mmapbench%d'%(i))
                if ret != 0:
                    raise Exception('cgroup creation failed')
                # TODO: set pg cache limit correctly 
                ret = os.system('echo %d > /sys/fs/cgroup/memory/mmapbench%d/memory.limit_in_bytes'%(pgcache_limit, i))
                if ret != 0:
                    raise Exception('Setting cgroup memory limit failed')


        # Clear page cache
        ret = os.system('echo 1 > /proc/sys/vm/drop_caches')
        if ret != 0:
            raise Exception('Failed to clear page cache')
        

    def run(self, duration):
        ssd_offsets = [0 for _ in range(len(self.ssds))]
        ssd_idx = 0
        core_idx = 0
        for i in self.cores:
            for j in range(self.threads_per_core):
                out_f = open(self.output_path + ('-core%d-thread%d'%(i, j)), 'w')
                # sudo cgexec -g memory:foo taskset -c 1 ./mmapbench WriteOneByte 60 /dev/sdc 0 $((10*1024*1024*1024))
                args = []
                #args += ['cgexec', '-g', 'memory:mmapbench', 'numactl', '--membind', str(self.mem_numa), '--physcpubind', str(i), self.mmapbench_path]
                cg = 'memory:mmapbench%d'%(core_idx*self.threads_per_core + j) if self.cg_per_process else 'memory:mmapbench'
                args += ['cgexec', '-g', cg, 'taskset', '-c', str(i), self.mmapbench_path]
            
                workload_str = ''
                if self.write_frac == 0:
                    workload_str += 'Read'
                elif self.write_frac == 100:
                    workload_str += 'Write'

                if self.pattern == 'sequential':
                    workload_str += 'All'
                    if self.instsize == 64:
                        workload_str += '64'
                elif self.pattern == 'sequential_onebyte':
                    workload_str += 'OneByte'

                args.append(workload_str)
                args.append(str(duration))

                # Round robin across SSDs
                fpath = os.path.join(self.ssds[ssd_idx], 'datafile%d'%(ssd_offsets[ssd_idx]))
                if not os.path.exists(fpath):
                    print(fpath)
                    raise Exception('Datafile does not exist')
                args.append(fpath)
                # Always map from offset 0. There appears to be a perf regression when mmaping from non-zero offset
                args.append(str(0))
                args.append(str(self.area_size))
                ssd_offsets[ssd_idx] += 1
                ssd_idx = (ssd_idx + 1)%len(self.ssds)


                my_env = os.environ.copy()

                # if self.hugepages:
                #     my_env['STREAM_HUGEPAGES'] = 'on'
                
                self.procs.append(subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT, env=my_env))
            core_idx += 1

    def wait(self):
        for p in self.procs:
            p.wait()

    def cleanup(self):
        for p in self.procs:
            p.kill()

    def set_instsize(self, size):
        if size not in [64]:
            raise Exception('Instruction size not supported')
        self.instsize = size

    def set_pattern(self, pattern):
        if pattern not in ['sequential', 'sequential_onebyte']:
            raise Exception('Pattern not supported')
        self.pattern = pattern
    
    def set_hugepages(self, val):
        if val:
            raise Exception('Hugepages not yet supported')
        self.hugepages = val
    
    def set_writefrac(self, val):
        if not val in [0, 100]:
            raise Exception('Write fraction not supported')

        self.write_frac = val
