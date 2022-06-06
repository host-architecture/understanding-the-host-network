import os, sys, re

STATS_PATH = '/home/midhul/membw-eval'
CORE_LIST=[0,4,8,12,16,20,24,28,1,5,9,13,17,21,25,29,2,6,10,14,18,22,26,30,3,7,11,15,19,23,27,31]
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
    with open(os.path.join(STATS_PATH, config + '.mlc.txt'), 'r') as f:
        for line in f:
            if not '0000' in line:
                continue
            cols = line.split()
            return float(cols[2])

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
                lfb_occ[i] = int(cols[3*i + 3])
                l1_cycles[i] = int(cols[3*i + 4])
                l1_misses[i] = int(cols[3*i + 5])
                core_lats[i] = 1e9*(float(lfb_occ[i])/float(l1_cycles[i]))/(float(l1_misses[i]))

    sum_lat = 0.0
    for i in range(min(num_cores, 8)):
        core_idx = CORE_LIST[i]
        sum_lat += core_lats[core_idx]

    return sum_lat/float(num_cores)

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
    for i in range(num_cores):
        miss_count += l1_misses[i]
        miss_count += l1_fbhits[i]
        total_count += all_loads[i]

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
    for i in range(num_cores):
        res += all_loads[i]

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
    for i in range(num_cores):
        miss_count += l2_misses[i]
        total_count += l2_hits[i]
        total_count += l2_misses[i]

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
    for i in range(num_cores):
        miss_count += l3_misses[i]
        total_count += l3_hits[i]
        total_count += l3_misses[i]

    return float(miss_count)/float(total_count)

def get_rpqocc(config):
    agg_occ = {}
    cycles = {}
    with open(os.path.join(STATS_PATH, config + '.pcm-imc.txt'), 'r') as f:
        for line in f:
            if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                continue
            cols = line.split(',')

            for i in range(NUM_CHANNELS):
                agg_occ[i] = int(cols[3*i + 3])
                cycles[i] = int(cols[3*i + 4])

    sum_occ = 0.0
    for i in range(NUM_CHANNELS):
        sum_occ += float(agg_occ[i])/float(cycles[i])

    
    return sum_occ/float(NUM_CHANNELS)




prefix = sys.argv[1]
core_range = sys.argv[2]
x_ncores = expand_ranges(core_range)

for i in x_ncores:
    config = prefix + '-cores' + str(i)
    row = '%d %f %f %f %f %f %f %d' % (i, get_xput(config), get_lfblat(config, i), get_l1miss(config, i), get_l2miss(config, i), get_l3miss(config, i), get_rpqocc(config), get_allloads(config, i))
    print(row)