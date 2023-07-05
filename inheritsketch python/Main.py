# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-03-28 11:26:10
# @Last Modified by:   xiegr
# @Last Modified time: 2023-07-05 18:43:06
from DTSketch import FakeDT, DTSketch
from TrafficTool import get_traffic_info
from Cal_Metrics import Cal_ARE_AAE_ASE_WRE_R2, \
	Cal_PRED_PRE_REC_F1_ACC, Cal_PRE_REC_F1_ACC
from time import time as Time
from OtherSketches.CountMin import CountMin
import numpy as np
from multiprocessing import Pool
from multiprocessing.managers import BaseManager
import sys
import time
import pandas as pd

TOP = [1000, 3000]
PKTS = 1000000

def predict_cls(dt_obj, features, k=8):
	# features consume too much mem, should be divided during using multiprocess
	k = k
	tmplen = len(features) // k

	Cls0 = []
	for i in range(k):
		Cls0.extend(dt_obj.predict(features[i*tmplen:(i+1)*tmplen]))
	if len(Cls0) < len(features):
		Cls0.extend(dt_obj.predict(features[(i+1)*tmplen:]))
	
	return np.array(Cls0)

def insert_sketch(idx, npy_name, flowid_name, top, dt_obj=None, name='All'):
	sk_obj = DTSketch(primary_mem=36*1024, cm_mem=128*1024, multi_hash=3)

	features = np.load(npy_name)[:PKTS, :8]
	flowids = np.load(flowid_name)[:PKTS]
	keys, occurences = np.unique(flowids, return_counts=True)
	Real_Freq = dict(zip(keys, occurences))

	# insert
	if name != 'All':
		Cls0 = predict_cls(dt_obj, flowids)
		list(
			map(lambda x: sk_obj.insert(x[0], x[1], x[2]), zip(flowids, features, Cls0))
		)
		X, Y = sk_obj.features_for_FK(top)
		dt_obj.train(X, Y, name)
	else:
		list(
			map(lambda x: sk_obj.insert(x[0], x[1]), zip(flowids, features))
		)

	# print info
	if idx == 0:
		get_traffic_info(Real_Freq, npy_name)
	sk_obj.get_primary_info(name)

	# overall metric
	ARE, AAE, ASE, WRE, R2 = Cal_ARE_AAE_ASE_WRE_R2(Real_Freq, sk_obj, -1)
	# top k metric
	ARE_1, AAE_1, ASE_1, WRE_1, R2_1 = Cal_ARE_AAE_ASE_WRE_R2(Real_Freq, sk_obj, top)
	# sketch collect top k metric
	PRE, REC, F1, ACC = Cal_PRE_REC_F1_ACC(Real_Freq, sk_obj, top)

	if name == 'All':
		return ARE, AAE, ASE, WRE, R2, ARE_1, AAE_1, ASE_1, WRE_1, R2_1, PRE, REC, F1, ACC, sk_obj.resub
	else:
		# predict top k metric
		PRE_1, REC_1, F1_1, ACC_1 = Cal_PRED_PRE_REC_F1_ACC(Real_Freq, top, flowids, Cls0) if name != 'FK' else Cal_PRE_REC_F1_ACC(Real_Freq, dt_obj, top)
		return ARE, AAE, ASE, WRE, R2, ARE_1, AAE_1, ASE_1, WRE_1, R2_1, PRE, REC, F1, ACC, PRE_1, REC_1, F1_1, ACC_1, sk_obj.resub


def main(pcap_prefix, pcap_root, pcap_format, top, start=0, end=30):
	columns1=[]
	columns1.extend(['All']*15) # without inheritance
	columns1.extend(['FK']*19) # inheritance
	columns2=[
	'ARE', 'AAE', 'ASE', 'WRE', 'R2', 'ARE_1', 'AAE_1', 'ASE_1', 'WRE_1', 'R2_1', 'PRE', 'REC', 'F1', 'ACC', 'ReSub',
	'ARE', 'AAE', 'ASE', 'WRE', 'R2', 'ARE_1', 'AAE_1', 'ASE_1', 'WRE_1', 'R2_1', 'PRE', 'REC', 'F1', 'ACC', 'PRE_1', 'REC_1', 'F1_1', 'ACC_1', 'ReSub',
	]


	df = pd.DataFrame(columns=[columns1, columns2])
	manager = BaseManager()
	manager.register('FakeDT', FakeDT)
	manager.start()

	fk = manager.FakeDT()

	for idx in range(start, end):
		print('\n====== Min: %d ======'%idx)
		localtime = time.asctime(time.localtime(Time()))
		print(pcap_prefix, localtime)

		t0 = Time()
		npy_name = pcap_root + pcap_format%idx
		flowid_name = pcap_root + (pcap_format%idx).replace('.npy', '.flowid.npy')
		
		# add process pool
		p = Pool(3)
		results = []
		results.append(
			p.apply_async(insert_sketch, 
				args=(0, npy_name, flowid_name, top, None, 'All', )))
		results.append(
			p.apply_async(insert_sketch, 
				args=(3, npy_name, flowid_name, top, fk, 'FK', )))
		p.close()
		p.join()
		
		# write results
		metrics = []
		for obj in results:
			metrics.extend(obj.get())
			# print(len(metrics), len(columns), '========')

		df.loc[idx] = metrics
		df.to_csv('results_d=3_thresh=50/dtsketch_info_%d_%s.csv'%(top, pcap_prefix), float_format='%.4f')

		# time?
		print('time(min): ', (Time()-t0)/60)


if __name__ == '__main__':
	for top in TOP:
		main(pcap_prefix='caida19', pcap_root='/data/xgr/sketch_data/caida_dirA/',\
		pcap_format='equinix-nyc.dirA.20190117-13%02d00.UTC.anon.npy', top=top)
		main(pcap_prefix='caida18', pcap_root='/data/xgr/traces/caidadirA/',\
		pcap_format='equinix-nyc.dirA.20180315-13%02d00.UTC.anon.npy', top=top)		
		main(pcap_prefix='cernet', pcap_root='/data/xgr/traces/cernet/',\
		pcap_format='20201227_14%02d00_ingress.npy', top=top)
