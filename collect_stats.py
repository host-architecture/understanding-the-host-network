import sys, os, glob
import argparse

from mio.env import *
from mio.stats import *
import mio.model as model

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


root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
config_path = os.path.join(root_dir, 'config.json')
env = Environment(config_path)

parser = argparse.ArgumentParser()
parser.add_argument('config', help='Label for experiment')
parser.add_argument('columns', help='Metrics to collect. Comma separated. <core/imc/io>:<metric>:<agg>')
default_core_list = ','.join([str(x) for x in env.get_cores_in_numa(env.get_numa_order()[0])])
parser.add_argument('--filter_core_list', help='List of cores to filter metrics on', default=default_core_list)
parser.add_argument('--filter_num_cores', help='Number of cores from filter_core_list to filter on', type=int, default=1)
parser.add_argument('--filter_channels', help='List of memory channels to filter on', default=','.join(env.get_mem_channels()))
parser.add_argument('--agg_time', help='Aggregation in time dimension', default='avg')
parser.add_argument('--io_size', help='IO size for FIO', type=int, default=8*1024*1024)
parser.add_argument('--filter_chas', help='List of CHAs to filter metrics on', default=','.join(env.get_chas()))
parser.add_argument('--filter_irps', help='List of IRPs to filter metrics on', default=','.join(env.get_irps()))
default_ssds = ['SSD%d'%(i) for i in range(len(env.get_ssds()))]
parser.add_argument('--filter_ssds', help='List of SSDs to filter metrics on', default=default_ssds)
parser.add_argument('--model', help='Apply model')

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

filepath= os.path.join(STATS_PATH, args.config + '.pcm-wpq.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-rpq.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-rpq2.txt')
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

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha2.txt')
if os.path.isfile(filepath):
        ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha3.txt')
if os.path.isfile(filepath):
            ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha4.txt')
if os.path.isfile(filepath):
            ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha5.txt')
if os.path.isfile(filepath):
            ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha6.txt')
if os.path.isfile(filepath):
            ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha7.txt')
if os.path.isfile(filepath):
            ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-cha8.txt')
if os.path.isfile(filepath):
                ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-mesh1.txt')
if os.path.isfile(filepath):
                ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-mesh2.txt')
if os.path.isfile(filepath):
                ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-mesh3.txt')
if os.path.isfile(filepath):
                ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-irp.txt')
if os.path.isfile(filepath):
    ss.load_pcm_raw(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.pcm-irp2.txt')
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

filepath= os.path.join(STATS_PATH, args.config + '.redis.txt')
if len(glob.glob(filepath + '-core*')) > 0:
    ss.load_redis(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.mmapbench.txt')
if len(glob.glob(filepath + '-core*')) > 0:
    ss.load_mmapbench(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.sar.txt')
if os.path.isfile(filepath):
    ss.load_sar(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.gapbs.txt')
if os.path.isfile(filepath):
    ss.load_gapbs(filepath)

filepath= os.path.join(STATS_PATH, args.config + '.gapbs-bc.txt')
if os.path.isfile(filepath):
        ss.load_gapbs(filepath)

filter_cores = args.filter_core_list.split(',')
filter_cores = filter_cores[:args.filter_num_cores]
filter_cores = ['CORE' + x for x in filter_cores]

filter_channels = args.filter_channels.split(',')
filter_chas = args.filter_chas.split(',')
filter_irps = args.filter_irps.split(',')
filter_io = args.filter_ssds.split(',')

cols = args.columns.split(',')
res = []
for col in cols:
    elems = col.split(':')
    metric_type = elems[0]
    if metric_type == 'model':
        model_name = elems[1]
        model_metric = elems[2]

        # Pass on filters
        filters = {
            'cores': filter_cores,
            'channels': filter_channels,
            'chas': filter_chas,
            'irps': filter_irps,
            'io': filter_io
        }

        res += model.query(ss, model_name, model_metric, filters)

    else:
        metric = elems[1]
        metric_agg = elems[2]

        metric_filter = None
        if metric_type == 'core':
            metric_filter = filter_cores
        elif metric_type == 'imc':
            metric_filter = filter_channels
        elif metric_type == 'cha':
            metric_filter = filter_chas
        elif metric_type == 'irp':
            metric_filter = filter_irps
        elif metric_type == 'io':
            metric_filter = filter_io

        res += ss.query(metric, agg_space=metric_agg, agg_time=args.agg_time, filter=metric_filter)

print(' '.join([str(x) for x in res]))
