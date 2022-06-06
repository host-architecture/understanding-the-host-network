from .env import *
from .mlc import *
from .pcm import *

import os

def main(args=[]):
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(root_dir, 'config.json')

    env = Environment(config_path)

    mlc = MLCRunner(env.get_mlc_path())
    mlc.init(os.path.join(env.get_stats_path(), 'foo.mlc.txt'), [0], 0, {})

    pcm_mem = PcmMemoryRunner(env.get_pcm_path())

    mlc.run(10)
    pcm_mem.run(os.path.join(env.get_stats_path(), 'foo.pcm-memory.txt'), 5)
    mlc.wait()

    print('Complete')
