# -*- coding: utf-8 -*-
# @Author: xgr19
# @Date:   2022-05-11 17:23:33
# @Last Modified by:   xiegr
# @Last Modified time: 2023-07-05 18:59:37
from Cal_Metrics import Cal_ARE_AAE_ASE_WRE_R2, \
	Cal_PRED_PRE_REC_F1_ACC, Cal_PRE_REC_F1_ACC
from time import time as Time
from OtherSketches.CountMin import CountMin
from OtherSketches.HashPipe import HashPipe
from OtherSketches.Precision import PRECISION
from OtherSketches.HashFlow import HashFlow
from OtherSketches.Count import Count
from OtherSketches.CU import CU
from OtherSketches.Elastic.Elastic import Elastic
from OtherSketches.ElasticP4 import ElasticP4
import numpy as np
from multiprocessing import Pool
import sys
import time
import pandas as pd

TOP = [1000, 3000]
PKTS = 1000000

def insert_sketch(flowid_name, top, name='HashFlow'):
	sk_objs = {
		'HashFlow': HashFlow(mem1=36*1024, mem2=128*1024), # 2^9 x 3, 2^17
		'HashPipe': HashPipe(mem1=36*1024, mem2=128*1024),
		'PRECISION': PRECISION(mem1=36*1024, mem2=128*1024, d=2),
		'Elastic': Elastic(mem1=36*1024, mem2=128*1024),
		'ElasticP4': ElasticP4(mem1=36*1024, mem2=128*1024),
		'CountMin': CountMin(36*1024+128*1024),
		'Count': Count(36*1024+128*1024),
		'CU': CU(36*1024+128*1024),
	}
	sk_obj = sk_objs[name]

	flowids = np.load(flowid_name)[:PKTS]
	keys, occurences = np.unique(flowids, return_counts=True)
	Real_Freq = dict(zip(keys, occurences))

	# insert
	list(
		map(lambda x: sk_obj.insert(x), flowids)
	)

	# overall metric
	ARE, AAE, ASE, WRE, R2 = Cal_ARE_AAE_ASE_WRE_R2(Real_Freq, sk_obj, -1)
	# top k metric
	ARE_1, AAE_1, ASE_1, WRE_1, R2_1 = Cal_ARE_AAE_ASE_WRE_R2(Real_Freq, sk_obj, top)
	# sketch collect top k metric
	PRE, REC, F1, ACC = Cal_PRE_REC_F1_ACC(Real_Freq, sk_obj, top)

	return ARE, AAE, ASE, WRE, R2, ARE_1, AAE_1, ASE_1, WRE_1, R2_1, PRE, REC, F1, ACC, sk_obj.resub


# 第0步，查看流分布
# 第一步，确定怎么训练DT
def main(pcap_prefix, pcap_root, pcap_format, top, start=0, end=30):
	names = ['HashFlow', 'HashPipe', 'PRECISION','Elastic', 'ElasticP4', 'CountMin', 'Count', 'CU']
	tmp = ['ARE', 'AAE', 'ASE', 'WRE', 'R2', 'ARE_1', 'AAE_1', 'ASE_1', 
	'WRE_1', 'R2_1', 'PRE', 'REC', 'F1', 'ACC', 'ReSub']

	columns1=[]
	for n in names:
		columns1.extend([n]*len(tmp))

	columns2=[]
	for _ in names:
		columns2.extend(tmp)

	df = pd.DataFrame(columns=[columns1, columns2])


	for idx in range(start, end):
		print('\n====== Min: %d ======'%idx)
		localtime = time.asctime(time.localtime(Time()))
		print(pcap_prefix, localtime)

		t0 = Time()
		npy_name = pcap_root + pcap_format%idx
		flowid_name = pcap_root + (pcap_format%idx).replace('.npy', '.flowid.npy')
		
		# add process pool
		p = Pool(len(names))
		results = []
		for n in names:
			results.append(
				p.apply_async(insert_sketch, args=(flowid_name, top, n, )))
		p.close()
		p.join()
		
		# write results
		metrics = []
		for obj in results:
			metrics.extend(obj.get())
			# print(len(metrics), len(columns), '========')

		df.loc[idx] = metrics
		df.to_csv('resultsother_double/sketch_info_%d_%s.csv'%(top, pcap_prefix), float_format='%.4f')

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
		# # 6min
		# main(pcap_prefix='HGC', pcap_root='/data/xgr/traces/HGC/',\
		# pcap_format='200904100%02d.npy', top=top, start=1, end=29)