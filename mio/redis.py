from .antagonist import *

import subprocess, os, time

class RedisRunner(Antagonist):
    def __init__(self, path, memtier_path):
        self.redis_server_path = os.path.join(path, 'redis-server')
        self.redis_client_path = os.path.join(path, 'redis-benchmark')
        self.memtier_path = os.path.join(memtier_path, 'memtier_benchmark')

    def init(self, output_path, cores, mem_numa, opts):
        self.output_path = output_path
        if(len(cores)%2 != 0):
            raise Exception('RedisRunner expects even number of cores')
        self.server_cores = cores[:len(cores)//2]
        self.mem_numa = mem_numa
        self.opts = opts

        # Default parameters (TODO: Parameterize)
        self.num_keys_per_core = 1000000
        self.num_accesses_per_core = 50000000
        self.num_clients_per_core = 2
        self.write_frac = 0
        self.value_size = 1024
        self.pipeline = 32
        #self.client_cores = [0,4,8,12,16,20,24,28]
        self.client_cores = cores[len(cores)//2:]
        self.client_numa = mem_numa

        self.procs = [] # This is for clients
        self.server_procs = [] # this is for servers

        # Kill an previous redis instances
        os.system('pkill -9 -f redis-server')
        time.sleep(5)
        os.system('rm -f /tmp/redis.sock*')

        # TODO disable THP etc. before starting redis

        # Start servers
        for i in self.server_cores:
            out_f = open(self.output_path + ('.server-core%d'%(i)), 'w')
            # numactl --membind 3 --physcpubind 3 ./redis-server --save "" --appendonly no --port 0 --bind 127.0.0.1 --unixsocket /tmp/redis.sock --unixsocketperm 755
            args = ['numactl', '--membind', str(self.mem_numa), '--physcpubind', str(i), self.redis_server_path, '--save', '""', '--appendonly', 'no', '--port', '0', '--bind', '127.0.0.1', '--unixsocket', ('/tmp/redis.sock%d'%(i)), '--unixsocketperm', '755']
            self.server_procs.append(subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT))

        # print('redis servers started')

        # Wait for servers to startup
        time.sleep(10)


        # Fill servers with data
        memtier_procs = []
        for i in self.server_cores:
            out_f = open(self.output_path + ('.memtier-core%d'%(i)), 'w')
            #numactl --membind 0 --physcpubind 0 ~/memtier_benchmark/memtier_benchmark -S /tmp/redis.sock --threads=1 --clients=2 --ratio=1:0 --distinct-client-seed -d 1024 -R --key-pattern=P:P --key-maximum=1000000 --pipeline=32 -n allkeys --hide-histogram --key-prefix="key:"
            args = [self.memtier_path, '-S', '/tmp/redis.sock%d'%(i), '--threads=1', '--clients=2', '--ratio=1:0', '--distinct-client-seed', '-d', str(self.value_size), '-R', '--key-pattern=P:P', '--key-maximum=%d'%(self.num_keys_per_core), '--pipeline=%d'%(self.pipeline), '-n', 'allkeys', '--hide-histogram', '--key-prefix=key:']
            memtier_procs.append(subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT))

        for p in memtier_procs:
            p.wait()

        time.sleep(3)

        # print('memtier complete')
        

    def run(self, duration):
        workload = 'get'
        print(self.write_frac)
        if self.write_frac == 100:
            workload = 'set'
        # Duration is ignored (not supported for now)
        for i, j in zip(self.client_cores, self.server_cores):
            out_f = open(self.output_path + ('-core%d'%(j)), 'w')
        # numactl --membind 0 --physcpubind 0 ./redis-benchmark -c 2 -n 100000000 -d 1024 -r 1000000 -t get -P 128
            args = []
            args += ['numactl', '--membind', str(self.client_numa), '--physcpubind', str(i), self.redis_client_path, '-s', '/tmp/redis.sock%d'%(j), '-c', str(self.num_clients_per_core), '-n', str(self.num_accesses_per_core), '-d', str(self.value_size), '-r', str(self.num_keys_per_core), '-t', workload, '-P', str(self.pipeline)]
            self.procs.append(subprocess.Popen(args, stdout=out_f, stderr=subprocess.STDOUT))

    def wait(self):
        for p in self.procs:
            p.wait()
        for p in self.server_procs:
            p.kill()

    def cleanup(self):
        for p in self.procs:
            p.kill()
        for p in self.server_procs:
            p.kill()

    def set_instsize(self, size):
        raise Exception('Not supported')

    def set_pattern(self, pattern):
        raise Exception('Not supported')
    
    def set_hugepages(self, val):
        raise Exception('Not supported')
    
    def set_writefrac(self, val):
        if val in [0, 100]:
            self.write_frac = val
        else:
            raise Exception('Not supported')
