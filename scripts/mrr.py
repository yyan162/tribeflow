#-*- coding: utf8
from __future__ import division, print_function

from node_sherlock import _learn
from node_sherlock.mycollections.stamp_lists import StampLists
import node_sherlock
import pandas as pd
import plac
import numpy as np

def main(model, out_fpath):
    store = pd.HDFStore(model)
    
    from_ = store['from_'][0][0]
    to = store['to'][0][0]
    assert from_ == 0
    
    trace_fpath = store['trace_fpath'][0][0]
    kernel_class = store['kernel_class'][0][0]
    kernel_class = eval(kernel_class)

    Theta_zh = store['Theta_zh'].values
    Psi_sz = store['Psi_sz'].values
    count_z = store['count_z'].values[:, 0]
    P = store['P'].values
    residency_priors = store['residency_priors'].values[:, 0]
    
    previous_stamps = StampLists(count_z.shape[0])
    tstamps = store['Dts'].values[:, 0]
    assign = store['assign'].values[:, 0]
    for z in xrange(count_z.shape[0]):
        idx = assign == z
        previous_stamps._extend(z, tstamps[idx])

    hyper2id = dict(store['hyper2id'].values)
    obj2id = dict(store['source2id'].values)
    
    HSDs = []
    tstamps = []

    with open(trace_fpath) as trace_file:
        for i, l in enumerate(trace_file): 
            if i < to:
                continue

            dt, h, s, d = l.strip().split('\t')
            if h in hyper2id and s in obj2id and d in obj2id:
                HSDs.append([hyper2id[h], obj2id[s], obj2id[d]])
                tstamps.append(float(dt))
    
    trace_size = sum(count_z)
    kernel = kernel_class()
    kernel.build(trace_size, count_z.shape[0], residency_priors)
    kernel.update_state(P)
    
    num_queries = min(10000, len(HSDs))
    queries = np.random.choice(len(HSDs), size=num_queries)

    HSDs = np.array(HSDs, dtype='i4')[queries].copy()
    tstamps = np.array(tstamps, dtype='d')[queries].copy()
    rrs = _learn.reciprocal_rank(tstamps, \
            HSDs, previous_stamps, Theta_zh, Psi_sz, count_z, kernel)
    
    np.savetxt(out_fpath, rrs)
    store.close()
    
plac.call(main)
