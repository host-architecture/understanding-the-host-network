from .env import *
from .mlc import *
from .pcm import *

import os, time
import argparse
import atexit

WARMUP_DURATION = 10
RECORD_DURATION = 5
RECORD_GROUPS = 5

events_group_0 = {'lfb_occ': 'core/config=0x0000000000430148', 'lfb_cycles': 'core/config=0x0000000001430148', 'load_l1_misses': 'core/config=0x00000000004308d1'}
events_group_1 = {'load_l1_hits': 'core/config=0x00000000004301d1', 'load_l1_misses': 'core/config=0x00000000004308d1', 'load_l1_fbhit': 'core/config=0x00000000004340d1', 'loads': 'core/config=0x00000000004381d0'}
events_group_2 = {'load_l2_hits': 'core/config=0x00000000004302d1', 'load_l2_misses': 'core/config=0x00000000004310d1', 'load_l3_hits': 'core/config=0x00000000004304d1', 'load_l3_misses': 'core/config=0x00000000004320d1'}
events_group_3 = {'rpq_occupancy': 'imc/config=0x0000000000400080', 'rpq_ne_cycles': 'imc/config=0x0000000000400011', 'cas_count': 'imc/config=0x000000000040f04'}

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
    mem_region = args.ant_mem_region
    numa_order = [int(x) for x in args.ant_numa_order.split(',')]
    ant_duration = args.ant_duration

    if args.ant and args.stats and ant_duration <= WARMUP_DURATION + RECORD_DURATION*RECORD_GROUPS:
        raise Exception('Duration too small for measuring all stats')

    print('Running %s-cores%d'%(prefix, num_cores))

    env.enable_prefetch()

    if args.disable_prefetch:
        env.disable_prefetch()

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

        ant.init(os.path.join(env.get_stats_path(), '%s-cores%d.mlc.txt'%(prefix, num_cores)), cores, mem_numa, mem_region, {})
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
        pcm_raw = PcmRawRunner(env.get_pcm_path())
#         pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-lfb.txt'%(prefix, num_cores)), events_group_0, RECORD_DURATION)
        pcm_latency = PcmLatencyRunner(env.get_pcm_path())
        pcm_latency.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-latency.txt'%(prefix, num_cores)), RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-l1.txt'%(prefix, num_cores)), events_group_1, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-l2l3.txt'%(prefix, num_cores)), events_group_2, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-imc.txt'%(prefix, num_cores)), events_group_3, RECORD_DURATION)

    
    if ant:
        ant.wait()

def cleanup():
    # TODO: Hacky
    os.system('pkill -9 -f pcm')
    os.system('pkill -9 -f mlc')
    os.system('pkill -9 -f fio')


def main(argv=[]):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(root_dir, 'config.json')

    atexit.register(cleanup)

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
    parser.add_argument('--ant_mem_region', help='Antagonist memory region size', default='1g')
    parser.add_argument('--stats', help='Record stats', action='store_true')
    parser.add_argument('--disable_prefetch', help='Disable prefetchers', action='store_true')

    args = parser.parse_args(argv[1:])
    x_ncores = expand_ranges(args.ant_num_cores)

    env = Environment(config_path)

    for x in x_ncores:
        args.ant_num_cores = x
        run_benchmark(args, env)

