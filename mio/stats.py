import os, sys, re, subprocess, glob

class StatStore:
    def __init__(self):
        self.d = {}

        self.derived_metrics = {
            'lfb_latency': (lambda x, y, z: 1e9*(x/y)/z, ['lfb_occ_agg', 'lfb_cycles', 'lfb_l1_misses']),
            'lfb_occupancy': (lambda x, y: x/y, ['lfb_occ_agg', 'lfb_cycles']),
            'lfb_fillfrac': (lambda x, y: x/y, ['lfb_full', 'lfb_cycles']),
            'l1_missrate': (lambda x, y, z: (x+y)/z, ['load_l1_misses', 'load_l1_fbhit', 'loads']),
            'l2_missrate': (lambda x, y: (x)/(x+y), ['load_l2_misses', 'load_l2_hits']),
            'l3_missrate': (lambda x, y: (x)/(x+y), ['load_l3_misses', 'load_l3_hits']),
            'rpq_occupancy': (lambda x: x/1466500000.0, ['rpq_occ_agg'])
        }

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

    def load_stream(self, filepath):
        stream_files = glob.glob(filepath + '-core*')
        if not 'stream_xput' in self.d:
            self.d['stream_xput'] = {}
        for sfile in stream_files:
            core_idx = int(re.match('.*-core(\d+)$', sfile)[1])
            space_unit = 'CORE%d' % (core_idx)
            if not space_unit in self.d['stream_xput']:
                self.d['stream_xput'][space_unit] = []
            with open(sfile, 'r') as f:
                for line in f:
                    if not 'Throughput' in line:
                        continue
                    cols = line.split()
                    self.d['stream_xput'][space_unit].append(float(cols[2]))

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
        self.d['fio_xput'] = {'ALL': float(subprocess.check_output(['./collect_fio.sh', config, str(io_size)]))}

    def compute_metric(self, metric):
        if not metric in self.derived_metrics:
            raise Exception('Unknown metric')

        func = self.derived_metrics[metric][0]
        input_metrics = self.derived_metrics[metric][1]

        self.d[metric] = {}
        for space_unit in self.d[input_metrics[0]]:
            self.d[metric][space_unit] = []
            for i in range(len(self.d[input_metrics[0]][space_unit])):
                input_metric_vals = []
                for j in range(len(input_metrics)):
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
            return sum([res[x] for x in res])
        elif agg_space == 'avg':
            return sum([res[x] for x in res]) / float(len(res))
        else:
            raise Exception('unknown agg_space')

