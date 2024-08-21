import sys, os

from mio.stats import *

STATS_PATH = '/home/sosp24ae/colloid-eval'

config = sys.argv[1]

ss = StatStore()

ss.load_pcm_raw(os.path.join(STATS_PATH, config + '.pcm-lfb.txt'))
ss.load_stream(os.path.join(STATS_PATH, config + '.stream.txt'))

print(ss.query('stream_xput', agg_space='sum', agg_time='sum', filter=['CORE3']))