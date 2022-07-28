import os, sys, re, subprocess

STATS_PATH = '/home/midhul/membw-eval'
CORE_LIST=[3,7,11,15,19,23,27,31,0,4,8,12,16,20,24,28,1,5,9,13,17,21,25,29,2,6,10,14,18,22,26,30]
NUM_CHANNELS=6

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


def get_xput(config):
    with open(os.path.join(STATS_PATH, config + '.mlc2.txt'), 'r') as f:
        for line in f:
            if not '0000' in line:
                continue
            cols = line.split()
            return float(cols[2])

def get_stream_xput(config, num_cores, start_core_num=0):
    xput = 0.0
    for i in range(start_core_num, start_core_num + num_cores):
        core_idx = CORE_LIST[i]
        with open(os.path.join(STATS_PATH, config + '.stream.txt-core' + str(core_idx)), 'r') as f:
            for line in f:
                if not 'Throughput' in line:
                    continue
                cols = line.split()
                xput += float(cols[2])
    return xput

def get_l1misslat(config, num_cores):
    core_lats = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-latency.txt'), 'r') as f:
        for line in f:
            if not re.search('Core\d+:', line):
                continue
            cols = line.split()
            if len(cols) % 2 != 0:
                raise Exception('Parsing error')
            for i in range(0, len(cols), 2):
                m = re.match('Core(\d+):', cols[i])
                if not m:
                    raise Exception('Parsing error')
                core_idx = int(m[1])
                core_lats[core_idx] = float(cols[i+1])
        
    sum_lat = 0.0
    for i in range(num_cores):
        core_idx = CORE_LIST[i]
        sum_lat += core_lats[core_idx]

    return sum_lat/float(num_cores)

def get_lfblat(config, num_cores):
    lfb_occ = {}
    l1_cycles = {}
    l1_misses = {}
    core_lats = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-lfb.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(len(CORE_LIST)):
                lfb_occ[i] = int(cols[4*i + 3])
                l1_cycles[i] = int(cols[4*i + 4])
                l1_misses[i] = int(cols[4*i + 5])
                core_lats[i] = 1e9*(float(lfb_occ[i])/float(l1_cycles[i]))/(float(l1_misses[i]))

    sum_lat = 0.0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        sum_lat += core_lats[core_idx]

    return sum_lat/float(num_cores)

def get_lfbocc(config, num_cores):
    lfb_occ = {}
    l1_cycles = {}
    l1_misses = {}
    core_occ = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-lfb.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(len(CORE_LIST)):
                lfb_occ[i] = int(cols[4*i + 3])
                l1_cycles[i] = int(cols[4*i + 4])
                l1_misses[i] = int(cols[4*i + 5])
                core_occ[i] = (float(lfb_occ[i])/float(l1_cycles[i]))

    sum_occ = 0.0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        sum_occ += core_occ[core_idx]

    return sum_occ/float(num_cores)

def get_lfbfull(config, num_cores):
    l1_cycles = {}
    lfb_full = {}
    core_lfb_full = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-lfb.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(len(CORE_LIST)):
                l1_cycles[i] = int(cols[4*i + 4])
                lfb_full[i] = int(cols[4*i + 6])
                core_lfb_full[i] = (float(lfb_full[i])/float(l1_cycles[i]))

    sum_lfb_full = 0.0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        sum_lfb_full += core_lfb_full[core_idx]

    return sum_lfb_full/float(num_cores)

def get_l1miss(config, num_cores):
    all_loads = {}
    l1_hits = {}
    l1_misses = {}
    l1_fbhits = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-l1.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(len(CORE_LIST)):
                l1_hits[i] = int(cols[4*i + 3])
                l1_misses[i] = int(cols[4*i + 4])
                l1_fbhits[i] = int(cols[4*i + 5])
                all_loads[i] = int(cols[4*i + 6])

    miss_count = 0
    total_count = 0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        miss_count += l1_misses[core_idx]
        miss_count += l1_fbhits[core_idx]
        total_count += all_loads[core_idx]

    return float(miss_count)/float(total_count)

def get_allloads(config, num_cores):
    all_loads = {}
    l1_hits = {}
    l1_misses = {}
    l1_fbhits = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-l1.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(len(CORE_LIST)):
                l1_hits[i] = int(cols[4*i + 3])
                l1_misses[i] = int(cols[4*i + 4])
                l1_fbhits[i] = int(cols[4*i + 5])
                all_loads[i] = int(cols[4*i + 6])

    res = 0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        res += all_loads[core_idx]

    return res

def get_l2miss(config, num_cores):
    l2_hits = {}
    l2_misses = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-l2l3.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(len(CORE_LIST)):
                l2_hits[i] = int(cols[4*i + 3])
                l2_misses[i] = int(cols[4*i + 4])

    miss_count = 0
    total_count = 0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        miss_count += l2_misses[core_idx]
        total_count += l2_hits[core_idx]
        total_count += l2_misses[core_idx]

    return float(miss_count)/float(total_count+1)

def get_l3miss(config, num_cores):
    l3_hits = {}
    l3_misses = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-l2l3.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(len(CORE_LIST)):
                l3_hits[i] = int(cols[4*i + 5])
                l3_misses[i] = int(cols[4*i + 6])

    miss_count = 0
    total_count = 0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        miss_count += l3_misses[core_idx]
        total_count += l3_hits[core_idx]
        total_count += l3_misses[core_idx]

    return float(miss_count)/float(total_count+1)

def get_rpqocc(config):
    numa_node = 3
    channel_whitelist = [1,4]
    agg_occ = {}
    cycles = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-imc.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
                channel_idx = (i - numa_node * NUM_CHANNELS + 1)
                if not channel_idx in channel_whitelist:
                    continue

                agg_occ[i] = int(cols[4*i + 3])
                cycles[i] = int(cols[4*i + 4])

    sum_occ = 0.0
    for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
        channel_idx = (i - numa_node * NUM_CHANNELS + 1)
        if not channel_idx in channel_whitelist:
            continue
        sum_occ += float(agg_occ[i])/1466500000.0

    return sum_occ / float(len(channel_whitelist))

def get_actcount(config):
    numa_node = 3
    channel_whitelist = [1,4]
    acts = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-imc.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
                channel_idx = (i - numa_node * NUM_CHANNELS + 1)
                if not channel_idx in channel_whitelist:
                    continue

                acts[i] = int(cols[4*i + 6])

    sum_acts = 0
    for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
        channel_idx = (i - numa_node * NUM_CHANNELS + 1)
        if not channel_idx in channel_whitelist:
            continue
        sum_acts += acts[i]

    
    return sum_acts

def get_actcount_write(config):
    numa_node = 3
    channel_whitelist = [1,4]
    acts = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-modes.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
                channel_idx = (i - numa_node * NUM_CHANNELS + 1)
                if not channel_idx in channel_whitelist:
                    continue

                acts[i] = int(cols[4*i + 6])

    sum_acts = 0
    for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
        channel_idx = (i - numa_node * NUM_CHANNELS + 1)
        if not channel_idx in channel_whitelist:
            continue
        sum_acts += acts[i]

    
    return sum_acts

def get_rmmcycles(config):
    numa_node = 3
    channel_whitelist = [1,4]
    acts = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-modes.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
                channel_idx = (i - numa_node * NUM_CHANNELS + 1)
                if not channel_idx in channel_whitelist:
                    continue

                acts[i] = int(cols[4*i + 3])

    sum_acts = 0.0
    for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
        channel_idx = (i - numa_node * NUM_CHANNELS + 1)
        if not channel_idx in channel_whitelist:
            continue
        sum_acts += acts[i]

    
    return sum_acts / float(len(channel_whitelist))

def get_wmmcycles(config):
    numa_node = 3
    channel_whitelist = [1,4]
    acts = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-modes.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
                channel_idx = (i - numa_node * NUM_CHANNELS + 1)
                if not channel_idx in channel_whitelist:
                    continue

                acts[i] = int(cols[4*i + 4])

    sum_acts = 0.0
    for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
        channel_idx = (i - numa_node * NUM_CHANNELS + 1)
        if not channel_idx in channel_whitelist:
            continue
        sum_acts += acts[i]

    
    return sum_acts / float(len(channel_whitelist))

def get_wmmtormm(config):
    numa_node = 3
    channel_whitelist = [1,4]
    acts = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-modes.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
                channel_idx = (i - numa_node * NUM_CHANNELS + 1)
                if not channel_idx in channel_whitelist:
                    continue

                acts[i] = int(cols[4*i + 5])

    sum_acts = 0.0
    for i in range(numa_node * NUM_CHANNELS, (numa_node+1)*NUM_CHANNELS):
        channel_idx = (i - numa_node * NUM_CHANNELS + 1)
        if not channel_idx in channel_whitelist:
            continue
        sum_acts += acts[i]

    
    return sum_acts / float(len(channel_whitelist))

def get_memreadbw(config):
    samples = []
    with open(os.path.join(STATS_PATH, config + '.pcm-memory.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')
            
            samples.append(float(cols[-3].strip()))
        
    return sum(samples) / float(len(samples))

def get_memwritebw(config):
    samples = []
    with open(os.path.join(STATS_PATH, config + '.pcm-memory.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')
            
            samples.append(float(cols[-2].strip()))
        
    return sum(samples) / float(len(samples))

def get_fioxput(config, io_size):
    return float(subprocess.check_output(['./collect_fio.sh', config, str(io_size)]))





prefix = sys.argv[1]
core_range = sys.argv[2]
io_size = 8*1024*1024
x_ncores = expand_ranges(core_range)

for i in x_ncores:
    config = prefix + '-cores' + str(i)
    # row = '%d %f %f %f %f %f %f %f %f %f %f %d' % (i, get_xput(config), get_memreadbw(config), get_memwritebw(config), get_lfblat(config, i), get_lfbocc(config, i), get_lfbfull(config, i), get_l1miss(config, i), get_l2miss(config, i), get_l3miss(config, i), get_rpqocc(config), get_allloads(config, i))
    # row = '%d %f %f %f %f' % (i, get_fioxput(config, io_size), get_memreadbw(config), get_memwritebw(config), get_stream_xput(config, i, 1))
    # row = '%d %f %f %f %f %f %f %f %f %f %f' % (i, get_fioxput(config, io_size), get_memreadbw(config), get_memwritebw(config),  get_rpqocc(config), get_allloads(config, i), get_actcount(config), get_rmmcycles(config), get_wmmcycles(config), get_wmmtormm(config), get_actcount_write(config))
    # row = '%d %f %f %f %f %f %f %f %f %f %f %d %d %f %f %f %d' % (i, get_stream_xput(config, i), get_memreadbw(config), get_memwritebw(config), get_lfblat(config, i), get_lfbocc(config, i), get_lfbfull(config, i), get_l1miss(config, i), get_l2miss(config, i), get_l3miss(config, i), get_rpqocc(config), get_allloads(config, i), get_actcount(config), get_rmmcycles(config), get_wmmcycles(config), get_wmmtormm(config), get_actcount_write(config))
    # row = '%d %f %f %f %f %f %f %f %f %f %f %f %d %d %f %f %f %d' % (i, get_fioxput(config, io_size), get_stream_xput(config, i), get_memreadbw(config), get_memwritebw(config), get_lfblat(config, i), get_lfbocc(config, i), get_lfbfull(config, i), get_l1miss(config, i), get_l2miss(config, i), get_l3miss(config, i), get_rpqocc(config), get_allloads(config, i), get_actcount(config), get_rmmcycles(config), get_wmmcycles(config), get_wmmtormm(config), get_actcount_write(config))
    row = '%d %f %f %f %f %f %f %f %f %f %d %d %f %f %f %d' % (i, get_memreadbw(config), get_memwritebw(config), get_lfblat(config, i), get_lfbocc(config, i), get_lfbfull(config, i), get_l1miss(config, i), get_l2miss(config, i), get_l3miss(config, i), get_rpqocc(config), get_allloads(config, i), get_actcount(config), get_rmmcycles(config), get_wmmcycles(config), get_wmmtormm(config), get_actcount_write(config))
    print(row)

# for i in x_ncores:
#     config = prefix + '-ssds' + str(i) + '-cores1'
#     row = '%d %f %f %f' % (i, get_fioxput(config, io_size), get_memreadbw(config), get_memwritebw(config))
#     print(row)