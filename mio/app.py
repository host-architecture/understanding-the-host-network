from .env import *
from .mlc import *
from .pcm import *

import os, time
import argparse

WARMUP_DURATION = 5
RECORD_DURATION = 5

def expand_ranges(x):
    result = []
    for part in x.split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            result.extend(range(a, b + 1))
        else:
            a = int(part)
            result.append(a)
    return result

def run_benchmark(args, env):
    prefix = args.config
    num_cores = args.ant_num_cores
    mem_numa = args.ant_mem_numa
    numa_order = [int(x) for x in args.ant_numa_order.split(',')]
    ant_duration = args.ant_duration

    print('Running %s-cores%d'%(prefix, num_cores))

    ant = None

    if args.ant:
        cores = []
        for numa_idx in numa_order:
            cores += env.get_cores_in_numa(numa_idx)
        cores = cores[:num_cores]

        if args.ant == 'mlc':
            ant = MLCRunner(env.get_mlc_path())
        else:
            raise Exception('Unknown antagonist')

        ant.init(os.path.join(env.get_stats_path(), '%s-cores%d.mlc.txt'%(prefix, num_cores)), cores, mem_numa, {})
        if args.ant_inst_size:
            ant.set_instsize(args.ant_inst_size)
        if args.ant_pattern:
            ant.set_pattern(args.ant_pattern)
        if args.ant_writefrac:
            ant.set_writefrac(args.ant_writefrac)

        ant.run(ant_duration)

    if args.stats:    
        pcm_mem = PcmMemoryRunner(env.get_pcm_path())
        time.sleep(WARMUP_DURATION)
        pcm_mem.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-memory.txt'%(prefix, num_cores)), RECORD_DURATION)

    
    if ant:
        ant.wait()


def main(argv=[]):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(root_dir, 'config.json')

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Label for experiment')
    parser.add_argument('--ant', help='What antagonist to use (mlc/stream)')
    parser.add_argument('--ant_num_cores', help='Number of cores to run antagonist on', default='1')
    parser.add_argument('--ant_mem_numa', help='Number of cores to run antagonist on', type=int, default=0)
    parser.add_argument('--ant_numa_order', help='Order of NUMA nodes to use for antagonist', default='0,1,2,3')
    parser.add_argument('--ant_inst_size', help='Instruction size for antagonist', type=int)
    parser.add_argument('--ant_pattern', help='Antagonist access pattern')
    parser.add_argument('--ant_writefrac', help='Antagonist write fraction (percentage)', type=int)
    parser.add_argument('--ant_duration', help='Antagonist run duration', type=int, default=40)
    parser.add_argument('--stats', help='Record stats', action='store_true')

    args = parser.parse_args(argv[1:])
    x_ncores = expand_ranges(args.ant_num_cores)

    env = Environment(config_path)

    for x in x_ncores:
        args.ant_num_cores = x
        run_benchmark(args, env)

