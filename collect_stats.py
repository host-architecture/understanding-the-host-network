import sys, os, glob
import argparse

from mio.stats import *

STATS_PATH = '/home/midhul/membw-eval'

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


parser = argparse.ArgumentParser()
parser.add_argument('config', help='Label for experiment')
parser.add_argument('columns', help='Metrics to collect. Comma separated. <core/imc/io>:<metric>:<agg>')
parser.add_argument('--filter_core_list', help='List of cores to filter metrics on', default='3,7,11,15,19,23,27,31')
parser.add_argument('--filter_num_cores', help='Number of cores from filter_core_list to filter on', type=int, default=1)
parser.add_argument('--filter_channels', help='List of memory channels to filter on', default='SKT3CHAN0,SKT3CHAN3')
parser.add_argument('--agg_time', help='Aggregation in time dimension', default='avg')
parser.add_argument('--io_size', help='IO size for FIO', type=int, default=8*1024*1024)

args = parser.parse_args(sys.argv[1:])

ss = StatStore()

filepath= os.path.join(STATS_PATH, args.config + '.pcm-memory.txt')
if os.path.isfile(filepath):
    ss.load_pcm_mem(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-latency.txt')
if os.path.isfile(filepath):
    ss.load_pcm_latency(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-lfb.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-l1.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-l2l3.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-imc.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-modes.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cas.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-pre.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.stream.txt')
if len(glob.glob(filepath + '-core*')) > 0:
    ss.load_stream(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.stream2.txt')
if len(glob.glob(filepath + '-core*')) > 0:
    ss.load_stream(filepath, label='stream2_xput')

filepath= os.path.join(STATS_PATH, args.config + '.mlc.txt')
if os.path.isfile(filepath):
    ss.load_mlc(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.fio*.txt')
if len(glob.glob(filepath)) > 0:
    ss.load_fio(args.config, args.io_size)

filter_cores = args.filter_core_list.split(',')
filter_cores = filter_cores[:args.filter_num_cores]
filter_cores = ['CORE' + x for x in filter_cores]

filter_channels = args.filter_channels.split(',')

cols = args.columns.split(',')
res = []
for col in cols:
    elems = col.split(':')
    metric_type = elems[0]
    metric = elems[1]
    metric_agg = elems[2]

    metric_filter = None
    if metric_type == 'core':
        metric_filter = filter_cores
    elif metric_type == 'imc':
        metric_filter = filter_channels

    res += ss.query(metric, agg_space=metric_agg, agg_time=args.agg_time, filter=metric_filter)

print(' '.join([str(x) for x in res]))
