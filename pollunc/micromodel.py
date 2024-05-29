import sys, os

CHA_FREQ = 2.4*1e9
IMC_FREQ_PRAC = 1463000000.0
IRP_FREQ = 0.5*1e9

NUM_CHANNELS = 2
T_CAS = 14.32
# T_PRE = 15.0
T_PRE = 14.32
# T_RAS = 38.19
T_RAS = 32
# T_ACT = 15.0
T_ACT = 14.32
T_Trans = 2.73
# T_Trans = 2.73*2
# T_FAW = 23.19
# T_FAW = 0.0
T_FAW = 21.14
# T_FAW = 21
T_Switch = 8.18
T_Write = 2.73
T_Read = 2.73
T_CWL = 13.64
T_WR = 15
# T_Write = 5.0
NBa = 32
NRa = 2

CONST_READ_CPU = 71
CONST_WRITE_CPU = 10
CONST_WRITE_IO = 317
CONST_CREDIT_PROP = 0

CHA_SCALE_FACTOR = 2.0

def compute_writelatio(x):
    td_ns = x['td_ns']
    lines_read = x['lines_read']
    lines_written = x['lines_written']
    pfillwpq = (x['pfillwpq34']/NUM_CHANNELS)/(td_ns*IMC_FREQ_PRAC*1e-9)
    wbmtoi_occ = CHA_SCALE_FACTOR * x['wbmtoi_occ']/(td_ns*CHA_FREQ*1e-9)
    blemon_occ = CHA_SCALE_FACTOR * x['blemon_occ']/(td_ns*CHA_FREQ*1e-9)
    wbmtoi_inserts = CHA_SCALE_FACTOR * x['wbmtoi_inserts']
    blemon_inserts = CHA_SCALE_FACTOR * x['blemon_inserts']
    iio_occ = x['iio_wr_occ']/(td_ns*IRP_FREQ*1e-9)
    iio_inserts = (x['pcie_rate']*4)/64.0

    avg_waiting = wbmtoi_occ + blemon_occ

    switching = 0.0
    rowmiss = 0.0
    readhol = (lines_read/lines_written) * T_Read 

    d = {}
    d['latency'] = CONST_WRITE_IO + pfillwpq*((avg_waiting/NUM_CHANNELS)*(switching + readhol + T_Trans) + rowmiss)
    d['pfillwpq'] = pfillwpq
    d['avg_waiting'] = avg_waiting
    d['readhol'] = readhol
    d['cha_wr_latency'] = avg_waiting/((blemon_inserts+wbmtoi_inserts)/td_ns)
    d['blemon_latency'] = blemon_occ/(blemon_inserts/td_ns)
    d['wbmtoi_latency'] = wbmtoi_occ/(wbmtoi_inserts/td_ns)
    d['iio_latency'] = iio_occ/(iio_inserts/td_ns)
    d['iio_occ'] = iio_occ
    d['pcie_bw'] = (iio_inserts*64)/td_ns

    return d
    

inputfile = sys.argv[1]

# Format
# index td_ns pfillwpq34 lines_read lines_written wbmtoi_occ wbmtoi_inserts blemon_occ blemon_inserts iio_wr_occ pcie_rate
header = ['idx', 'td_ns', 'pfillwpq34', 'lines_read', 'lines_written', 'wbmtoi_occ', 'wbmtoi_inserts', 'blemon_occ', 'blemon_inserts', 'iio_wr_occ', 'pcie_rate']
d = []
with open(inputfile, 'r') as f:
    for line in f:
        if len(line) == 0:
            continue
        dd = {}
        cols = line.split()
        for i in range(len(cols)):
            dd[header[i]] = float(cols[i])
        d.append(dd)


for dd in d:
    res = compute_writelatio(dd)
    print('%f %f %f %f %f'%(res['iio_latency'], res['blemon_latency'], res['latency'], res['iio_occ'], res['pcie_bw']))


