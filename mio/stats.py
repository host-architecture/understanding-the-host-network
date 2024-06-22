import os, sys, re, subprocess, glob
from mio.env import *

class StatStore:
    def __init__(self):
        # Set configs
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
        config_path = os.path.join(root_dir, 'config.json')
        env = Environment(config_path)
        self.max_ssds = len(env.get_ssds())
        self.fio_stats_path = env.get_stats_path()
        self.cha_freq = env.get_cha_freq()
        self.imc_freq = env.get_imc_freq()

        self.d = {}

        # CascadeLake
        self.derived_metrics = {
            'lfb_latency': (lambda x, y, z: 1e9*(x/y)/z, ['lfb_occ_agg', 'lfb_cycles', 'lfb_l1_misses']),
            'l1_miss_latency_adj': (lambda x, y: 1e9*(x/y), ['fb_occupancy', 'lfb_l1_misses']),
            'lfb_occupancy': (lambda x, y: x/y, ['lfb_occ_agg', 'lfb_cycles']),
            'lfb_fillfrac': (lambda x, y: x/y, ['lfb_full', 'lfb_cycles']),
            'l1_missrate': (lambda x, y, z: (x+y)/z, ['load_l1_misses', 'load_l1_fbhit', 'loads']),
            'l2_missrate': (lambda x, y: (x)/(x+y), ['load_l2_misses', 'load_l2_hits']),
            'l3_missrate': (lambda x, y: (x)/(x+y), ['load_l3_misses', 'load_l3_hits']),
            'rpq_occupancy': (lambda x: x/1466500000.0, ['rpq_occ_agg']),
            'switching_delay': (lambda z, x, y: x*(y/(z*1e6/64))*8.18, ['memreadbw', 'rpq_occupancy', 'wmm_to_rmm']),
            'write_hol': (lambda z, x, y: x*(y/z)*2.73, ['memreadbw', 'rpq_occupancy', 'memwritebw']),
            'act_penalty': (lambda z, x, y: ((x+y)/(z*1e6/64))*15, ['memreadbw', 'acts_read', 'acts_byp']),
            'pre_penalty': (lambda w, x, y, z: (x/(x+y))*(z/(w*1e6/64))*15, ['memreadbw', 'pre_miss', 'pre_close', 'pre_rd']),
            'remainder': (lambda x: max(x-1, 0) * 2.73, ['rpq_occupancy']),
            'row_miss_penalty': (lambda x, y: x + y, ['act_penalty', 'pre_penalty']),
            'estimated_qd': (lambda x,y,z,w: x + y + z + w, ['switching_delay', 'write_hol', 'row_miss_penalty', 'remainder']),
            'actual_qd': (lambda x: max(x - 71.3, 0), ['l1_miss_latency']),
            'estimated_latency': (lambda x: 71.3 + x, ['estimated_qd']),
            'read_activations': (lambda x, y: x + y, ['acts_read', 'acts_byp']),
            'cha_miss_latency': (lambda x, y, z: 1e9*(x/y)/z, ['tor_drd_miss_occ_agg', 'unc_clk', 'tor_drd_miss_inserts']),
            'irp_write_latency': (lambda x, y, z: 1e9*(x/(z+0.0000000005))/(y+0.0000000000005), ['irp_write_occupancy', 'write_inserts_pcitom', 'irp_cycles']),
            'irp_occupancy': (lambda x, y: x/(y+0.0000000000005), ['irp_write_occupancy', 'irp_cycles']),
            'io_xput': (lambda x: x/8.0, ['fio_xput']),
            'lines_read': (lambda x: (x - 228.5)*1e6/64, ['memreadbw']),
            'pre_conflict_read': (lambda x, y, z: (x*z)/(x+y), ['pre_miss', 'pre_close', 'pre_rd']),
            'acts_read_total': (lambda x, y: x + 4, ['acts_read', 'acts_byp']),
            'lines_written': (lambda x: x*1e6/64, ['memwritebw']),
            'drd_occupancy': (lambda x: x/self.cha_freq, ['drd_occ_agg']),
            'drd_latency': (lambda x, y: x*1e9/y, ['drd_occupancy', 'drd_inserts']),
            'wbeftoi_occupancy': (lambda x: x/self.cha_freq, ['wbeftoi_occ_agg']),
            'wbeftoi_latency': (lambda x, y: x*1e9/y, ['wbeftoi_occupancy', 'weftoi_inserts']),
            'wbmtoi_occupancy': (lambda x: x/self.cha_freq, ['wbmtoi_occ_agg']),
            'wbmtoi_latency': (lambda x, y: x*1e9/y, ['wbmtoi_occupancy', 'wbmtoi_inserts']),
            'pwbmtoi_occupancy': (lambda x: x/self.cha_freq, ['pwbmtoi_occ_agg']),
            'pwbmtoi_latency': (lambda x, y: x*1e9/(y+0.0000000000005), ['pwbmtoi_occupancy', 'pwbmtoi_inserts']),
            'itom_occupancy': (lambda x: x/self.cha_freq, ['itom_occ_agg']),
            'itom_latency': (lambda x, y: x*1e9/(y+0.0000000000005), ['itom_occupancy', 'itom_inserts']),
            'blemon_occupancy': (lambda x: x/self.cha_freq, ['blemon_occ_agg']),
            'blemon_latency': (lambda x, y: x*1e9/(y+0.0000000000005), ['blemon_occupancy', 'blemon_inserts']),
            'rdcur_occupancy': (lambda x: x/self.cha_freq, ['rdcur_occ_agg']),
            'rdcur_latency': (lambda x, y: x*1e9/(y+0.0000000000005), ['rdcur_occupancy', 'rdcur_inserts']),
            'pfillwpq30': (lambda x: x/self.imc_freq, ['wpq_occ_gte30']),
            'pfillwpq32': (lambda x: x/self.imc_freq, ['wpq_occ_gte32']),
            'pfillwpq34': (lambda x: x/self.imc_freq, ['wpq_occ_gte34']),
            'pfillwpq36': (lambda x: x/self.imc_freq, ['wpq_occ_gte36']),
            'pfillrpq38': (lambda x: x/self.imc_freq, ['rpq_occ_gte38']),
            'pfillrpq40': (lambda x: x/self.imc_freq, ['rpq_occ_gte40']),
            'pfillrpq42': (lambda x: x/self.imc_freq, ['rpq_occ_gte42']),
            'pfillrpq44': (lambda x: x/self.imc_freq, ['rpq_occ_gte44'])
        }

        # IceLake
        # self.derived_metrics = {
        #     'lfb_latency': (lambda x, y, z: 1e9*(x/y)/z, ['lfb_occ_agg', 'lfb_cycles', 'lfb_l1_misses']),
        #     'l1_miss_latency_adj': (lambda x, y: 1e9*(x/y), ['fb_occupancy', 'lfb_l1_misses']),
        #     'lfb_occupancy': (lambda x, y: x/y, ['lfb_occ_agg', 'lfb_cycles']),
        #     'lfb_fillfrac': (lambda x, y: x/y, ['lfb_full', 'lfb_cycles']),
        #     'l1_missrate': (lambda x, y, z: (x+y)/z, ['load_l1_misses', 'load_l1_fbhit', 'loads']),
        #     'l2_missrate': (lambda x, y: (x)/(x+y), ['load_l2_misses', 'load_l2_hits']),
        #     'l3_missrate': (lambda x, y: (x)/(x+y), ['load_l3_misses', 'load_l3_hits']),
        #     'rpq_occupancy': (lambda x, y: (x + y)/1600000000.0, ['rpq_occ_agg', 'rpq_occ_agg1']),
        #     'wpq_occupancy': (lambda x, y: (x + y)/1600000000.0, ['wpq_occ_agg', 'wpq_occ_agg1']),
        #     'io_xput': (lambda x: x/8.0, ['fio_xput'])
        # }

    def load_pcm_raw(self, filepath):
        # parse and load PCM raw output file
        space_units = []
        metrics = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith(',,,'):
                    space_units = line.split(',')
                    for j in range(len(space_units)):
                        if space_units[j].find('CORE') >= 0:
                            space_units[j] = space_units[j][space_units[j].find('CORE'):]
                    continue
                
                if line.startswith('Date,Time,'):
                    metrics = line.split(',')
                    continue

                if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                    continue

                cols = line.split(',')

                for i in range(3, len(cols)):
                    if cols[i].strip() == '':
                        continue

                    if metrics[i] not in self.d:
                        self.d[metrics[i]] = {}

                    if space_units[i] not in self.d[metrics[i]]:
                        self.d[metrics[i]][space_units[i]] = []

                    self.d[metrics[i]][space_units[i]].append(float(cols[i]))


    def load_pcm_mem(self, filepath):
        sockets = []
        metrics = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith(',,'):
                    sockets = line.split(',')
                    continue
                
                if line.startswith('Date,Time,'):
                    metrics = line.split(',')
                    continue

                if not re.search('\d\d\d\d-\d\d-\d\d,', line):
                    continue

                cols = line.split(',')

                for i in range(2, len(cols)):
                    if cols[i].strip() == '':
                        continue

                    space_unit = None
                    metric = None

                    if re.match('Ch(\d+)Read', metrics[i]):
                        ch_idx = re.match('Ch(\d+)Read', metrics[i])[1]
                        space_unit = sockets[i] + 'CHAN' + ch_idx
                        metric = 'memreadbw'
                    elif re.match('Ch(\d+)Write', metrics[i]):
                        ch_idx = re.match('Ch(\d+)Write', metrics[i])[1]
                        space_unit = sockets[i] + 'CHAN' + ch_idx
                        metric = 'memwritebw'
                    else:
                        continue
                        
                    if metric not in self.d:
                        self.d[metric] = {}

                    if space_unit not in self.d[metric]:
                        self.d[metric][space_unit] = []

                    self.d[metric][space_unit].append(float(cols[i].strip()))

    def load_sar(self, filepath):
        label = 'cpu_util'
        if not label in self.d:
            self.d[label] = {}
        with open(filepath, 'r') as f:
            for line in f:
                cols = line.split()
                if len(cols) < 1 or cols[0] != 'Average:':
                    continue
                if len(cols) < 2 or (not cols[1].isdigit()):
                    continue
                core_idx = int(cols[1])
                cpu_used = float(cols[2]) + float(cols[4])

                space_unit = 'CORE%d' % (core_idx)
                if not space_unit in self.d[label]:
                    self.d[label][space_unit] = []
                self.d[label][space_unit].append(cpu_used)


    def load_stream(self, filepath, label='stream_xput'):
        stream_files = glob.glob(filepath + '-core*')
        if not label in self.d:
            self.d[label] = {}
        for sfile in stream_files:
            core_idx = int(re.match('.*-core(\d+)$', sfile)[1])
            space_unit = 'CORE%d' % (core_idx)
            if not space_unit in self.d[label]:
                self.d[label][space_unit] = []
            with open(sfile, 'r') as f:
                for line in f:
                    if not 'Throughput' in line:
                        continue
                    cols = line.split()
                    self.d[label][space_unit].append(float(cols[2]))
    
    def load_mmapbench(self, filepath, label='mmapbench_xput'):
        stream_files = glob.glob(filepath + '-core*')
        if not label in self.d:
            self.d[label] = {}
        for sfile in stream_files:
            core_idx = int(re.match('.*-core(\d+)-thread(\d+)$', sfile)[1])
            # thread_idx = int(re.match('.*-core(\d+)-thread(\d+)$', sfile)[2])
            space_unit = 'CORE%d' % (core_idx)
            if not space_unit in self.d[label]:
                self.d[label][space_unit] = [0.0]
            with open(sfile, 'r') as f:
                for line in f:
                    if not 'Throughput' in line:
                        continue
                    cols = line.split()
                    self.d[label][space_unit][0] += float(cols[2])

    def load_mlc(self, filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if not '0000' in line:
                    continue
                cols = line.split()
                if not 'mlc_xput' in self.d:
                    self.d['mlc_xput'] = {}
                self.d['mlc_xput']['ALL'] = [float(cols[2])]

    def load_fio(self, config, io_size):
        # TODO: Parse fio directly instead of relying on bash script
        self.d['fio_xput'] = {}
        for i in range(self.max_ssds):
            if os.path.exists(os.path.join(self.fio_stats_path, '%s.fio%d.txt'%(config, i))):
                self.d['fio_xput']['SSD%d'%(i)] = [float(subprocess.check_output(['./collect_fio.sh', config, str(io_size), str(i)]))]

    def compute_metric(self, metric):
        if not metric in self.derived_metrics:
            raise Exception('Unknown metric')

        func = self.derived_metrics[metric][0]
        input_metrics = self.derived_metrics[metric][1]
        # Recursively compute derived input metrics
        for inp_metric in input_metrics:
            if not inp_metric in self.d and inp_metric in self.derived_metrics:
                # print('resursilvey computing metric: ' + inp_metric)
                self.compute_metric(inp_metric)

        self.d[metric] = {}
        for space_unit in self.d[input_metrics[0]]:
            self.d[metric][space_unit] = []
            for i in range(len(self.d[input_metrics[0]][space_unit])):
                input_metric_vals = []
                for j in range(len(input_metrics)):
                    if not space_unit in self.d[input_metrics[j]]:
                        print('Not found space unit')
                        print(space_unit)
                        print(input_metrics[j])
                        print(self.d[input_metrics[j]])
                    input_metric_vals.append(self.d[input_metrics[j]][space_unit][i])
                self.d[metric][space_unit].append(func(*input_metric_vals))

    def load_pcm_latency(self, filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if 'FB_Occupancy' in line:
                    cols = line.split(',')
                    for col in cols:
                        if col.strip() == '':
                            continue
                        space_unit = col.split(':')[1]
                        fb_occ_val = float(col.split(':')[2])
                        if not 'fb_occupancy' in self.d:
                            self.d['fb_occupancy'] = {}
                        if not space_unit in self.d['fb_occupancy']:
                            self.d['fb_occupancy'][space_unit] = []
                        self.d['fb_occupancy'][space_unit].append(fb_occ_val)
                    continue

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
                    if not 'l1_miss_latency' in self.d:
                        self.d['l1_miss_latency'] = {}
                    space_unit = 'CORE' + str(core_idx)
                    if not space_unit in self.d['l1_miss_latency']:
                        self.d['l1_miss_latency'][space_unit] = []
                    self.d['l1_miss_latency'][space_unit].append(float(cols[i+1]))

    def load_redis(self, filepath, label='redis_xput'):
        stream_files = glob.glob(filepath + '-core*')
        if not label in self.d:
            self.d[label] = {}
        for sfile in stream_files:
            core_idx = int(re.match('.*-core(\d+)$', sfile)[1])
            space_unit = 'CORE%d' % (core_idx)
            if not space_unit in self.d[label]:
                self.d[label][space_unit] = []
            with open(sfile, 'r') as f:
                for line in f:
                    if not 'throughput summary:' in line:
                        continue
                    cols = line.split()
                    self.d[label][space_unit].append(float(cols[2]))

    def load_gapbs(self, filepath):
        with open(filepath, 'r') as f:
            for line in f:
                if not 'Trial Time:' in line:
                    continue
                cols = line.split()
                if not 'gapbs_time' in self.d:
                    self.d['gapbs_time'] = {}
                    self.d['gapbs_time']['ALL'] = []
                self.d['gapbs_time']['ALL'].append(float(cols[2]))
            

    def query(self, metric, agg_space='avg', agg_time='avg', filter=None):
        if not metric in self.d and metric in self.derived_metrics:
            self.compute_metric(metric)

        if not metric in self.d:
            raise Exception('Metric unavailable')

        res = {}
        for space_unit in self.d[metric]:
            if filter == None or space_unit == 'ALL' or space_unit in filter:
                if agg_time == 'avg':
                    res[space_unit] = sum(self.d[metric][space_unit]) / float(len(self.d[metric][space_unit]))
                elif agg_time == 'sum':
                    res[space_unit] = sum(self.d[metric][space_unit])
                elif agg_time == 'last':
                    res[space_unit] = self.d[metric][space_unit][-1]
                else:
                    raise Exception('unknown agg_time')

        if agg_space == 'sum':
            return [sum([res[x] for x in res])]
        elif agg_space == 'avg':
            return [sum([res[x] for x in res]) / float(len(res))]
        elif agg_space == 'none':
            return [res[x] for x in res]
        else:
            raise Exception('unknown agg_space')
        
