from .stats import *
from scipy.stats import binom

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

def query(ss, model_name, model_metric, filters):
    res = {}
    if model_name == 'readlatcpu':
        compute_readlat(ss, res, filters, CONST_READ_CPU)
    elif model_name == 'readlatcpuadj':
        compute_readlat(ss, res, filters, CONST_READ_CPU, adj_pfillrpq=True)
    elif model_name == 'writelatio':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='sq')
    elif model_name == 'writelatcpu':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='sq')
    elif model_name == 'writelatio5':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='rr')
    elif model_name == 'writelatcpu5':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='rr')
    elif model_name == 'writelatio7':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='rr', xpr='adj')
    elif model_name == 'writelatcpu7':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='rr', xpr='adj')
    elif model_name == 'writelatio8':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='nq', xpr='adj')
    elif model_name == 'writelatcpu8':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='nq', xpr='adj')
    elif model_name == 'writelatio9':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='nq*', xpr='adj')
    elif model_name == 'writelatcpu9':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='nq*', xpr='adj')
    elif model_name == 'writelatio10':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='rr*', xpr='adj')
    elif model_name == 'writelatcpu10':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='rr*', xpr='adj')
    elif model_name == 'writelatio11':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='rr*', xpr='adj', pfillfactor=2)
    elif model_name == 'writelatcpu11':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='rr*', xpr='adj', pfillfactor=2)
    elif model_name == 'writelatcpu12':
        compute_writelat(ss, res, filters, CONST_WRITE_CPU, agent='cpu', sched='sq*', xpr='adj')
    elif model_name == 'writelatio42':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='enlightenment', xpr='adj')
    elif model_name == 'writelatio43':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='enlightenment', xpr='def')
    elif model_name == 'writelatio44':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='enlightenment', xpr='ub')
    elif model_name == 'writelatio45':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='enlightenment', xpr='bib')
    elif model_name == 'writelatio46':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='enlightenment', xpr='adj', pfilloverride=1.0)
    elif model_name == 'writelatio47':
        compute_writelat(ss, res, filters, CONST_WRITE_IO, agent='io', sched='enlightenment', xpr='adj', pfillmetric='pfillwpq34')
    else:
        raise Exception('Unknown model name')

    if not model_metric in res:
        raise Exception('Model metric does not exist')

    return [res[model_metric]]

def compute_readlat(ss, d, filters, const, adj_pfillrpq=False):

    rpq_occupancy = ss.query('rpq_occupancy', agg_space='avg', filter=filters['channels'])[0]
    switches = ss.query('wmm_to_rmm', agg_space='sum', filter=filters['channels'])[0]
    lines_read = (ss.query('memreadbw', agg_space='sum', filter=filters['channels'])[0] * 1e6) / 64.0
    lines_written = (ss.query('memwritebw', agg_space='sum', filter=filters['channels'])[0] * 1e6) / 64.0
    pre_conflict = ss.query('pre_miss', agg_space='sum', filter=filters['channels'])[0]
    read_acts = ss.query('acts_read', agg_space='sum', filter=filters['channels'])[0] + ss.query('acts_byp', agg_space='sum', filter=filters['channels'])[0]
    write_acts = ss.query('acts_write', agg_space='sum', filter=filters['channels'])[0]

    if adj_pfillrpq:
        pfillrpq = ss.query('pfillrpq42', agg_space='avg', filter=filters['channels'])[0]
        rdcur_occupancy = ss.query('rdcur_occupancy', agg_space='sum', filter=filters['chas'])[0]
        drd_occupancy = ss.query('drd_occupancy', agg_space='sum', filter=filters['chas'])[0]
        nwaiting = rdcur_occupancy + drd_occupancy
        rpq_occupancy = (1-pfillrpq)*rpq_occupancy + pfillrpq*(nwaiting/NUM_CHANNELS)

    res = 0.0

    switching = rpq_occupancy * (float(switches)/float(lines_read)) * T_Switch
    writehol = rpq_occupancy * (float(lines_written)/float(lines_read)) * T_Write
    # pre_conflict_read = (float(pre_conflict)/float(pre_conflict + pre_close))*float(read_acts)
    pre_conflict_read = float(pre_conflict)*((float(read_acts))/float(read_acts + write_acts))
    rowmiss = (float(read_acts)/float(lines_read))*T_ACT + (float(pre_conflict_read)/float(lines_read))*T_PRE
    remainder = max(0, rpq_occupancy-1)*T_Trans

    res += switching + writehol + rowmiss + remainder

    d['latency'] = const + res
    d['qd'] = res
    d['switching'] = switching
    d['writehol'] = writehol
    d['rowmiss'] = rowmiss
    d['remainder'] = remainder


def compute_writelat(ss, d, filters, const, agent='cpu', sched='sq', xpr='def', pfillfactor=1.0, pfilloverride=None, pfillmetric=None):

    switches = ss.query('wmm_to_rmm', agg_space='sum', filter=filters['channels'])[0]
    lines_read = (ss.query('memreadbw', agg_space='sum', filter=filters['channels'])[0] * 1e6) / 64.0
    lines_written = (ss.query('memwritebw', agg_space='sum', filter=filters['channels'])[0] * 1e6) / 64.0
    pre_conflict = ss.query('pre_miss', agg_space='sum', filter=filters['channels'])[0]
    read_acts = ss.query('acts_read', agg_space='sum', filter=filters['channels'])[0] + ss.query('acts_byp', agg_space='sum', filter=filters['channels'])[0]
    write_acts = ss.query('acts_write', agg_space='sum', filter=filters['channels'])[0]
    write_no_credits = ss.query('cha_write_no_credits', agg_space='sum', filter=filters['chas'])[0]
    lfb_sum = ss.query('fb_occupancy', agg_space='sum', filter=filters['cores'])[0]
    iio_occ = ss.query('irp_write_occupancy', agg_space='sum', filter=filters['irps'])[0] / ss.query('irp_cycles', agg_space='avg', filter=filters['irps'])[0]
    rpq_occupancy_total = ss.query('rpq_occupancy', agg_space='sum', filter=filters['channels'])[0]
    wbmtoi_occ = ss.query('wbmtoi_occupancy', agg_space='sum', filter=filters['chas'])[0]
    blemon_occ = ss.query('blemon_occupancy', agg_space='sum', filter=filters['chas'])[0]
    pfillwpq34 = ss.query('pfillwpq34', agg_space='avg', filter=[filters['channels'][0]])[0]

    res = 0.0

    switching = (float(switches)/float(lines_written)) * T_Switch
    readhol = (float(lines_read)/float(lines_written)) * T_Read
    # pre_conflict_read = (float(pre_conflict)/float(pre_conflict + pre_close))*float(read_acts)
    pre_conflict_write = float(pre_conflict)*((float(write_acts))/float(read_acts + write_acts))
    rowmiss = (float(write_acts)/float(lines_written))*T_ACT + (float(pre_conflict_write)/float(lines_written))*T_PRE
    pfillwpq = pfillfactor*(float(write_no_credits)/float(lines_written))
    if pfillmetric == 'pfillwpq34':
        pfillwpq = pfillwpq34
    if pfilloverride:
        pfillwpq = pfilloverride

    #res += pfillwpq*(float(nagents)/2)*(switching + readhol + rowmiss)
    # res += pfillwpq*(CONST_CREDIT_PROP + ((0.5*(lfb_sum + iio_occ))/NUM_CHANNELS)*(switching + readhol + rowmiss))
    avg_waiting = None
    if sched == 'sq':
        avg_waiting = 0.5*(lfb_sum + iio_occ)
    elif sched == 'sq*':
        avg_waiting = iio_occ + rpq_occupancy_total
    elif sched == 'rr':
        if agent == 'cpu':
            avg_waiting = lfb_sum
        else:
            avg_waiting = iio_occ
    elif sched == 'rr*':
        if agent == 'cpu':
            avg_waiting = 2*rpq_occupancy_total
        else:
            avg_waiting = 2*iio_occ
    elif sched == 'nq':
        lfb_avg = ss.query('fb_occupancy', agg_space='avg', filter=filters['cores'])[0]
        ncores = lfb_sum / lfb_avg
        if agent == 'cpu':
            avg_waiting = ((ncores + 1)*lfb_avg)/2
        else:
            avg_waiting = ((ncores + 1)*iio_occ)/2
    elif sched == 'nq*':
        lfb_avg = ss.query('fb_occupancy', agg_space='avg', filter=filters['cores'])[0]
        ncores = lfb_sum / lfb_avg
        if agent == 'cpu':
            avg_waiting = ((ncores + 1)*(rpq_occupancy_total/ncores))
        else:
            avg_waiting = ((ncores + 1)*iio_occ)
    elif sched == 'enlightenment':
        avg_waiting = wbmtoi_occ + blemon_occ
    else:
        raise Exception('Unknown sched')

    if xpr == 'def': 
        res += pfillwpq*(CONST_CREDIT_PROP + (avg_waiting/NUM_CHANNELS)*(switching + readhol + rowmiss))
    elif xpr == 'adj':
        res += pfillwpq*(CONST_CREDIT_PROP + (avg_waiting/NUM_CHANNELS)*(switching + readhol + T_Trans) + rowmiss)
    elif xpr == 'ub':
        res += pfillwpq*(avg_waiting/NUM_CHANNELS)*(switching + readhol + T_Trans + (float(write_acts)/float(lines_written))*(T_ACT + T_PRE + T_CWL + T_WR)*0.15)
    elif xpr == 'bib':
        maxexpr = 0
        Nwaiting = avg_waiting/NUM_CHANNELS
        n = max(0, round(Nwaiting))
        x = 0
        while x <= n:
            ba_comp = (float(pre_conflict_write)/float(lines_written))*T_PRE 
            ba_comp += (float(write_acts)/float(lines_written))*(x*T_ACT + x*T_CWL + x*T_Trans + x*T_WR + T_ACT)
            ch_comp = Nwaiting * T_Trans
            prob = float((binom.pmf(x, n, 1.0/float(NBa))))
            val = prob * max(ba_comp, ch_comp)
            maxexpr += val
            x += 1
        res += pfillwpq*(Nwaiting*switching + Nwaiting*readhol + maxexpr)
    # res += pfillwpq*(switching + readhol + rowmiss)

    d['latency'] = const + res
    d['ad'] = res
    d['switching'] = pfillwpq*(avg_waiting/NUM_CHANNELS)*switching
    d['readhol'] = pfillwpq*(avg_waiting/NUM_CHANNELS)*readhol
    d['rowmiss'] = pfillwpq*rowmiss
    d['writehol'] = pfillwpq*(avg_waiting/NUM_CHANNELS)*T_Trans
