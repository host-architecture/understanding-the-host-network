from mio.mmapbench import MmapBenchRunner
from mio.sar import SarRunner
from .env import *
from .mlc import *
from .pcm import *
from .fio import *
from .stream import *
from .redis import *
from .gapbs import *

import os, time
import argparse
import atexit

WARMUP_DURATION = 10
RECORD_DURATION = 5
RECORD_GROUPS = 15
FIO_PRESTART_DURATION = 0
ANT_WARMUP_DURATION = 10
ANT_COOLDOWN_DURATION = 10

# Cascadelake
events_group_0 = {'lfb_occ_agg': 'core/config=0x0000000000430148', 'lfb_cycles': 'core/config=0x0000000001430148', 'lfb_l1_misses': 'core/config=0x00000000004308d1', 'lfb_full': 'core/config=0x0000000000430248'}
events_group_1 = {'load_l1_hits': 'core/config=0x00000000004301d1', 'load_l1_misses': 'core/config=0x00000000004308d1', 'load_l1_fbhit': 'core/config=0x00000000004340d1', 'loads': 'core/config=0x00000000004381d0'}
events_group_2 = {'load_l2_hits': 'core/config=0x00000000004302d1', 'load_l2_misses': 'core/config=0x00000000004310d1', 'load_l3_hits': 'core/config=0x00000000004304d1', 'load_l3_misses': 'core/config=0x00000000004320d1'}
events_group_3 = {'rpq_occ_agg': 'imc/config=0x0000000000400080', 'wpq_full_cycles': 'imc/config=0x0000000000400022', 'acts_byp': 'imc/config=0x000000000040801', 'acts_read': 'imc/config=0x000000000040101'}
events_group_4 = {'wmm_to_rmm_starve': 'imc/config=0x0000000000402c0', 'wmm': 'imc/config=0x0000000000400207', 'wmm_to_rmm': 'imc/config=0x0000000000407c0', 'acts_write': 'imc/config=0x000000000040201'}
events_group_5 = {'wr_wmm': 'imc/config=0x0000000000400404', 'wr_rmm': 'imc/config=0x0000000000400804', 'rd_wmm': 'imc/config=0x000000000041004', 'rd_rmm': 'imc/config=0x000000000042004'}
events_group_6 = {'pre_miss': 'imc/config=0x000000000040102', 'pre_close': 'imc/config=0x000000000040202', 'pre_rd': 'imc/config=0x000000000040402', 'pre_wr': 'imc/config=0x000000000040802'}
#events_group_7 = {'tor_drd_miss_occ_agg': 'cha/config=0x0000000000402536,config2=0x40433', 'tor_drd_miss_inserts': 'cha/config=0x0000000000402535,config2=0x40433', 'unc_clk': 'cha/config=0x0000000000400000'}
events_group_7 = {'cha_write_no_credits': 'cha/config=0x000000000040035a', 'unc_clk': 'cha/config=0x0000000000400000'}
events_group_8 = {'write_inserts': 'irp/config=0x0000000000401810', 'irp_write_occupancy': 'irp/config=0x000000000040040f'}
events_group_9 = {'irp_cycles': 'irp/config=0x0000000000400001'}
events_group_10 = {'ia_wbmtoi_occ_agg': 'cha/config=0x0000000000403136,config2=0x48833'}
events_group_11 = {'io_itom_occ_agg': 'cha/config=0x0000000000403436,config2=0x49033'}
events_group_12 = {'cha_horz_bl_used': 'cha/config=0x0000000000400fab', 'cha_vert_bl_used': 'cha/config=0x0000000000400faa', 'cha_horx_ad_used': 'cha/config=0x0000000000400fa7', 'horz_ad_util': 'cha/config=0x0000000000400fa6'}
events_group_13 = {'cha_rxr_busy_starved': 'cha/config=0x00000000004084b4', 'cha_rxr_crd_starved': 'cha/config=0x00000000004044b3', 'cha_txr_horz_starved': 'cha/config=0x000000000040049b', 'cha_stall_txr_bl_ag1': 'cha/config=0x0000000000403fd6'}
events_group_14 = {'cha_txr_horz_nack': 'cha/config=0x0000000000404499', 'cha_txr_vert_nack': 'cha/config=0x0000000000404098', 'cha_txr_horx_occ': 'cha/config=0x0000000000404494', 'cha_rxr_occ': 'cha/config=0x00000000004044b0'}

# CHA events
# IMPORTANT: occupancy events can only be measured on counter 0
events_group_15 = {'drd_occ_agg': 'cha/config=0x0000000000402136,config2=0x40433', 'drd_inserts': 'cha/config=0x0000000000402135,config2=0x40433'}
events_group_16 = {'wbeftoi_occ_agg': 'cha/config=0x0000000000403136,config2=0x48c33', 'weftoi_inserts': 'cha/config=0x0000000000403135,config2=0x48c33'}
events_group_17 = {'wbmtoi_occ_agg': 'cha/config=0x0000000000403136,config2=0x48833', 'wbmtoi_inserts': 'cha/config=0x0000000000403135,config2=0x48833'}
events_group_18 = {'itom_occ_agg': 'cha/config=0x0000000000403436,config2=0x49033', 'itom_inserts': 'cha/config=0x0000000000403435,config2=0x49033'}
events_group_19 = {'blemon_occ_agg': 'cha/config=0x0000000000403436,config2=0x43033', 'blemon_inserts': 'cha/config=0x0000000000403435,config2=0x43033'}
events_group_23 = {'rdcur_occ_agg': 'cha/config=0x0000000000402436,config2=0x43c33', 'rdcur_inserts': 'cha/config=0x0000000000402435,config2=0x43c33'}
events_group_24 = {'pwbmtoi_occ_agg': 'cha/config=0x0000000000403436,config2=0x48833', 'pwbmtoi_inserts': 'cha/config=0x0000000000403435,config2=0x48833'}

# Events for PFillWPQ
events_group_20 = {'wpq_occ_gte34': 'imc/config=0x22400081', 'wpq_occ_gte30': 'imc/config=0x1e400081', 'wpq_occ_gte32': 'imc/config=0x20400081', 'wpq_occ_gte36': 'imc/config=0x24400081'}

# Events for PFillRPQ
events_group_21 = {'rpq_occ_gte32': 'imc/config=0x20400080', 'rpq_occ_gte34': 'imc/config=0x22400080', 'rpq_occ_gte36': 'imc/config=0x24400080', 'rpq_occ_gte38': 'imc/config=0x26400080'}
events_group_22 = {'rpq_occ_gte40': 'imc/config=0x28400080', 'rpq_occ_gte42': 'imc/config=0x2a400080', 'rpq_occ_gte44': 'imc/config=0x2c400080', 'rpq_occ_gte46': 'imc/config=0x2e400080'}

# Icelake
# events_group_0 = {'lfb_occ_agg': 'core/config=0x0000000000430148', 'lfb_cycles': 'core/config=0x0000000001430148', 'lfb_l1_misses': 'core/config=0x00000000004308d1', 'lfb_full': 'core/config=0x0000000000430248'}
# events_group_1 = {'load_l1_hits': 'core/config=0x00000000004301d1', 'load_l1_misses': 'core/config=0x00000000004308d1', 'load_l1_fbhit': 'core/config=0x00000000004340d1', 'loads': 'core/config=0x00000000004381d0'}
# events_group_2 = {'load_l2_hits': 'core/config=0x00000000004302d1', 'load_l2_misses': 'core/config=0x00000000004310d1', 'load_l3_hits': 'core/config=0x00000000004304d1', 'load_l3_misses': 'core/config=0x00000000004320d1'}
# events_group_3 = {'rpq_occ_agg': 'imc/config=0x0000000000400080', 'rpq_occ_agg1': 'imc/config=0x0000000000400081', 'wpq_occ_agg': 'imc/config=0x000000000040082', 'wpq_occ_agg1': 'imc/config=0x000000000040083'}

# SSD = ['/dev/nvme2n1', '/dev/nvme3n1', '/dev/nvme4n1', '/dev/nvme5n1', '/dev/nvme6n1', '/dev/nvme7n1']
# SSD = ['/dev/nvme0n1', '/dev/nvme1n1', '/dev/nvme2n1', '/dev/nvme3n1', '/dev/nvme4n1', '/dev/nvme5n1']
# sdb, sdc, sde, sdh, sdi, sdj, sdk
#SSD = ['/dev/sdc', '/dev/sde', '/dev/sdi', '/dev/sdj', '/dev/sdb', '/dev/sdh', '/dev/sdk']
SSD_MNTS = ['/mnt/sdc1', '/mnt/sde1', '/mnt/sdi1', '/mnt/sdj1', '/mnt/sdb1', '/mnt/sdh1', '/mnt/sdk1']

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

    if args.ant and args.stats and ant_duration <= WARMUP_DURATION + RECORD_DURATION*RECORD_GROUPS:
        raise Exception('Antagonist Duration too small for measuring all stats')

    if args.fio and args.stats_membw and args.fio_duration < WARMUP_DURATION + RECORD_DURATION:
        raise Exception('FIO Duration too small for measuring stats')

    if args.ant and args.fio and args.sync_durations and args.ant_duration + 2*(ANT_WARMUP_DURATION-FIO_PRESTART_DURATION) <= WARMUP_DURATION + RECORD_DURATION*RECORD_GROUPS:
        raise Exception('Duration too small for measuring all stats')
    
    os.system('rm ' + os.path.join(env.get_stats_path(), '%s.*'%(prefix)))

    print('Running %s-cores%d'%(prefix, num_cores))

    if not args.notouch_prefetch:
        env.enable_prefetch()

        if args.disable_prefetch:
            env.disable_prefetch()

        if args.disable_prefetch_l1:
            env.disable_prefetch_l1()

    ant = None

    if args.ant:
        cores = []
        if args.ant_cpus:
            cores += [int(y) for y in args.ant_cpus.split(',')]
        else:
            for numa_idx in numa_order:
                cores += env.get_cores_in_numa(numa_idx)
        if args.fio:
            fio_core_list = [int(y) for y in args.fio_cpus.split(',')]
            cores = [x for x in cores if x not in fio_core_list]
        cores = cores[:num_cores]

        if args.ant == 'mlc':
            ant = MLCRunner(env.get_mlc_path())
        elif args.ant == 'stream':
            ant = STREAMRunner(env.get_stream_path())
        elif args.ant == 'redis':
            ant = RedisRunner(env.get_redis_path(), env.get_memtier_path())
        elif args.ant == 'gapbs':
            ant = GAPBSRunner(env.get_gapbs_path(), 'pr')
        elif args.ant == 'gapbs-bc':
            ant = GAPBSRunner(env.get_gapbs_path(), 'bc')
        else:
            raise Exception('Unknown antagonist')

        ant_opts = {}
        if args.ant_chunksize:
            ant_opts['chunk_size'] = args.ant_chunksize

        if args.sync_durations:
            ant_opts['warmup_duration'] = ANT_WARMUP_DURATION
            ant_opts['cooldown_duration'] = ANT_COOLDOWN_DURATION

        ant.init(os.path.join(env.get_stats_path(), '%s-cores%d.%s.txt'%(prefix, num_cores, args.ant)), cores, mem_numa, ant_opts)
        if args.ant_inst_size:
            ant.set_instsize(args.ant_inst_size)
        if args.ant_pattern:
            ant.set_pattern(args.ant_pattern)
        if args.ant_writefrac:
            ant.set_writefrac(args.ant_writefrac)
        if args.ant_hugepages:
            ant.set_hugepages(True)

        ant.run(ant_duration)

    ant2 = None
    if args.ant2:
        cores2 = [int(x) for x in args.ant2_cpus.split(',')]
        cores2 = cores2[:args.ant2_num_cores]

        if args.ant2 == 'mlc':
            ant2 = MLCRunner(env.get_mlc_path())
        elif args.ant2 == 'stream':
            ant2 = STREAMRunner(env.get_stream_path())
        else:
            raise Exception('Unknown antagonist 2')

        ant2.init(os.path.join(env.get_stats_path(), '%s-cores%d.%s2.txt'%(prefix, num_cores, args.ant2)), cores2, args.ant2_mem_numa, {})
        if args.ant2_inst_size:
            ant2.set_instsize(args.ant2_inst_size)
        if args.ant2_pattern:
            ant2.set_pattern(args.ant2_pattern)
        if args.ant2_writefrac:
            ant2.set_writefrac(args.ant2_writefrac)
        if args.ant2_hugepages:
            ant2.set_hugepages(True)

        ant2.run(args.ant2_duration)

    fios = []
    if args.fio:
        SSD = env.get_ssds()
        if args.ant:
            time.sleep(FIO_PRESTART_DURATION)
        for i in range(args.fio_num_ssds):
            fio = FIORunner(env.get_fio_path())
            fio_core_list = [int(y) for y in args.fio_cpus.split(',')]
            fio.init(os.path.join(env.get_stats_path(), '%s-cores%d.fio%d.txt'%(prefix, num_cores, i)), [fio_core_list[i % len(fio_core_list)]], args.fio_mem_numa, args.fio_iosize, args.fio_iodepth, args.fio_writefrac, SSD[i])
            if args.fio_rate:
                print('Setting fio rate cap')
                fio.set_ratecap(args.fio_rate)
            fio_duration = args.fio_duration
            if args.ant and args.sync_durations:
                fio_duration = args.ant_duration + 2*(ANT_WARMUP_DURATION-FIO_PRESTART_DURATION)
            if args.fio_until_ant:
                fio_duration = 10000
            fio.run(fio_duration)
            fios.append(fio)

    mmapbench = None
    if args.mmapbench:
        if args.ant:
            time.sleep(FIO_PRESTART_DURATION)
        mmapbench = MmapBenchRunner(env.get_mmapbench_path())
        mmapbench_cores_str = args.mmapbench_cpus
        mmapbench_cores = None
        if 'NUMA' in mmapbench_cores_str:
            numa_node = int(mmapbench_cores_str[4:])
            mmapbench_cores = env.get_cores_in_numa(numa_node)
        else:
            mmapbench_cores = [int(y) for y in args.mmapbench_cpus.split(',')]
        mmapbench_cores = mmapbench_cores[:args.mmapbench_num_cores]
        mmapbench_ssds = SSD_MNTS[:args.mmapbench_num_ssds]

        mmapbench_opts = {}
        if args.mmapbench_cg_per_process:
            mmapbench_opts['cg_per_process'] = True
        mmapbench.init(os.path.join(env.get_stats_path(), '%s.mmapbench.txt'%(prefix)), mmapbench_cores, args.mmapbench_mem_numa, args.mmapbench_threads_per_core, mmapbench_ssds, args.mmapbench_areasize, args.mmapbench_pgcache_frac, mmapbench_opts)
        if args.mmapbench_inst_size:
            mmapbench.set_instsize(args.mmapbench_inst_size)
        if args.mmapbench_pattern:
            mmapbench.set_pattern(args.mmapbench_pattern)
        if args.mmapbench_writefrac:
            mmapbench.set_writefrac(args.mmapbench_writefrac)
        mmapbench.run(args.mmapbench_duration)


    # TODO: This needs cleanup
    if args.stats:    
        pcm_mem = PcmMemoryRunner(env.get_pcm_path())
        time.sleep(WARMUP_DURATION)
        pcm_mem.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-memory.txt'%(prefix, num_cores)), RECORD_DURATION)
        pcm_latency = PcmLatencyRunner(env.get_pcm_path())
        pcm_latency.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-latency.txt'%(prefix, num_cores)), RECORD_DURATION)
        pcm_raw = PcmRawRunner(env.get_pcm_path())
        # pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-lfb.txt'%(prefix, num_cores)), events_group_0, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha.txt'%(prefix, num_cores)), events_group_7, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha2.txt'%(prefix, num_cores)), events_group_15, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha3.txt'%(prefix, num_cores)), events_group_16, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha4.txt'%(prefix, num_cores)), events_group_17, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha5.txt'%(prefix, num_cores)), events_group_18, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha6.txt'%(prefix, num_cores)), events_group_19, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha7.txt'%(prefix, num_cores)), events_group_23, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cha8.txt'%(prefix, num_cores)), events_group_24, RECORD_DURATION)
        #pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-l1.txt'%(prefix, num_cores)), events_group_1, RECORD_DURATION)
        #pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-l2l3.txt'%(prefix, num_cores)), events_group_2, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-imc.txt'%(prefix, num_cores)), events_group_3, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-wpq.txt'%(prefix, num_cores)), events_group_20, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-rpq.txt'%(prefix, num_cores)), events_group_21, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-rpq2.txt'%(prefix, num_cores)), events_group_22, RECORD_DURATION)
        # Following only for CascadeLake. (comment out for IceLake)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-modes.txt'%(prefix, num_cores)), events_group_4, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-cas.txt'%(prefix, num_cores)), events_group_5, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-pre.txt'%(prefix, num_cores)), events_group_6, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-irp.txt'%(prefix, num_cores)), events_group_8, RECORD_DURATION)
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-irp2.txt'%(prefix, num_cores)), events_group_9, RECORD_DURATION)
        # pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-mesh1.txt'%(prefix, num_cores)), events_group_12, RECORD_DURATION)
        # pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-mesh2.txt'%(prefix, num_cores)), events_group_13, RECORD_DURATION)
        # pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-mesh3.txt'%(prefix, num_cores)), events_group_14, RECORD_DURATION)
    elif args.stats_membw:
        pcm_mem = PcmMemoryRunner(env.get_pcm_path())
        time.sleep(WARMUP_DURATION)
        pcm_mem.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-memory.txt'%(prefix, num_cores)), RECORD_DURATION)
    elif args.stats_single:
        # pcm_raw = PcmRawRunner(env.get_pcm_path())
        time.sleep(WARMUP_DURATION)
        # pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-imc.txt'%(prefix, num_cores)), events_group_3, args.stats_single_duration, granularity=args.stats_single_gran)
        #pcm_latency = PcmLatencyRunner(env.get_pcm_path())
        #pcm_latency.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-latency.txt'%(prefix, num_cores)), args.stats_single_duration)
#        pcm_mem = PcmMemoryRunner(env.get_pcm_path())
 #       pcm_mem.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-memory.txt'%(prefix, num_cores)), args.stats_single_duration)
        pcm_raw = PcmRawRunner(env.get_pcm_path())
        pcm_raw.run(os.path.join(env.get_stats_path(), '%s-cores%d.pcm-pre.txt'%(prefix, num_cores)), events_group_6, args.stats_single_duration)
    elif args.stats_cpuutil:
        time.sleep(WARMUP_DURATION)
        sar = SarRunner()
        sar.run(os.path.join(env.get_stats_path(), '%s.sar.txt'%(prefix)), RECORD_DURATION)





    if args.fio and not args.fio_until_ant:
        for fio in fios:
            fio.wait()

    if mmapbench:
        mmapbench.wait()

    if ant:
        ant.wait()

    if args.fio and args.fio_until_ant:
        for fio in fios:
            fio.end()
        for fio in fios:
            fio.wait()

    if ant2:
        ant2.wait()

def cleanup():
    # TODO: Hacky
    os.system('pkill -9 -f pcm')
    os.system('pkill -9 -f mlc')
    #os.system('pkill -9 -f fio')
    os.system('pkill -9 -f stream')
    os.system('pkill -9 -f redis-server')
    os.system('pkill -9 -f mmapbench')
    os.system('pkill -9 -f sar')



def main(argv=[]):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(root_dir, 'config.json')

    env = Environment(config_path)

    atexit.register(cleanup)

    default_numa = env.get_numa_order()[0]
    default_core = env.get_cores_in_numa(default_numa)[0] 

    parser = argparse.ArgumentParser()
    parser.add_argument('config', help='Label for experiment')
    parser.add_argument('--ant', help='What antagonist to use (mlc/stream)')
    parser.add_argument('--ant_cpus', help='List of CPUs to run antagonist on')
    parser.add_argument('--ant_num_cores', help='Number of cores to run antagonist on', default='1')
    parser.add_argument('--ant_mem_numa', help='NUMA node to allocate antagonist memory on', type=int, default=default_numa)
    parser.add_argument('--ant_numa_order', help='Order of NUMA nodes to use for antagonist', default=','.join([str(x) for x in env.get_numa_order()]))
    parser.add_argument('--ant_inst_size', help='Instruction size for antagonist', type=int)
    parser.add_argument('--ant_pattern', help='Antagonist access pattern')
    parser.add_argument('--ant_chunksize', help='Antagonist chunk size for random access pattern', type=int)
    parser.add_argument('--ant_writefrac', help='Antagonist write fraction (percentage)', type=int)
    parser.add_argument('--ant_duration', help='Antagonist run duration', type=int, default=40)
    parser.add_argument('--ant_prestart_duration', help='Time to wait before starting antagonist', type=int)
    parser.add_argument('--ant_hugepages', help='Enable hugepages', action='store_true')
    parser.add_argument('--stats', help='Record stats', action='store_true')
    parser.add_argument('--stats_membw', help='Record membw stats', action='store_true')
    parser.add_argument('--stats_cpuutil', help='Record CPU utilization stats', action='store_true')
    parser.add_argument('--disable_prefetch', help='Disable prefetchers', action='store_true')
    parser.add_argument('--disable_prefetch_l1', help='Disable L1 prefetchers', action='store_true')
    parser.add_argument('--fio', help='Run fio', action='store_true')
    parser.add_argument('--fio_mem_numa', help='what it says', type=int, default=default_numa)
    parser.add_argument('--fio_cpus', help='List of CPUs to run fio on', default=str(default_core))
    parser.add_argument('--fio_writefrac', help='what it says', type=int, default=0)
    parser.add_argument('--fio_iosize', help='what it says', type=int, default=4096)
    parser.add_argument('--fio_iodepth', help='what it says', type=int, default=1)
    parser.add_argument('--fio_num_ssds', help='what it says', type=int, default=1)
    parser.add_argument('--fio_duration', help='what it says', type=int, default=10)
    parser.add_argument('--fio_rate', help='what it says', type=int)
    parser.add_argument('--fio_until_ant', help='Run fio until ant is finished', action='store_true')
    parser.add_argument('--ant2', help='What antagonist to use (mlc/stream)')
    parser.add_argument('--ant2_cpus', help='List of cores to run antagonist on', default=str(default_core))
    parser.add_argument('--ant2_num_cores', help='Number of cores to run antagonist on', type=int, default=1)
    parser.add_argument('--ant2_mem_numa', help='Number of cores to run antagonist on', type=int, default=default_numa)
    parser.add_argument('--ant2_inst_size', help='Instruction size for antagonist', type=int)
    parser.add_argument('--ant2_pattern', help='Antagonist access pattern')
    parser.add_argument('--ant2_writefrac', help='Antagonist write fraction (percentage)', type=int)
    parser.add_argument('--ant2_duration', help='Antagonist run duration', type=int, default=40)
    parser.add_argument('--ant2_hugepages', help='Enable hugepages', action='store_true')
    parser.add_argument('--notouch_prefetch', help='Do not modify prefetchers', action='store_true')
    parser.add_argument('--stats_single', help='Record single statistic', action='store_true')
    parser.add_argument('--stats_single_duration', help='Record stats duration', type=int, default=5)
    parser.add_argument('--stats_single_gran', help='Record stats granularity', type=float, default=1.0)
    parser.add_argument('--sync_durations', help='Synchronize durations of apps', action='store_true')
    parser.add_argument('--mmapbench', help='Run mmapbench', action='store_true')
    parser.add_argument('--mmapbench_mem_numa', help='what it says', type=int, default=0)
    parser.add_argument('--mmapbench_cpus', help='List of CPUs to run mmapbench on', default='NUMA1')
    parser.add_argument('--mmapbench_num_cores', help='what it says', type=int, default=1)
    parser.add_argument('--mmapbench_writefrac', help='what it says', type=int, default=0)
    parser.add_argument('--mmapbench_num_ssds', help='what it says', type=int, default=1)
    parser.add_argument('--mmapbench_duration', help='what it says', type=int, default=10)
    parser.add_argument('--mmapbench_areasize', help='what it says', type=int, default=10*1024*1024*1024)
    parser.add_argument('--mmapbench_pgcache_frac', help='what it says', type=float, default=0.1)
    parser.add_argument('--mmapbench_threads_per_core', help='what it says', type=int, default=1)
    parser.add_argument('--mmapbench_inst_size', help='Instruction size for mmapbench', type=int)
    parser.add_argument('--mmapbench_pattern', help='mmapbench access pattern')
    parser.add_argument('--mmapbench_cg_per_process', help='One cgroup per process', action='store_true')


    args = parser.parse_args(argv[1:])
    x_ncores = expand_ranges(args.ant_num_cores)


    for x in x_ncores:
        args.ant_num_cores = x
        run_benchmark(args, env)

