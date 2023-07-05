# -*- coding: utf-8 -*-
# @Author: xiegr
# @Date:   2020-06-30 15:04:12
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-11 18:26:08
import numpy as np
from sklearn.metrics import precision_recall_fscore_support, accuracy_score
import sys

def Cal_ARE_AAE_ASE_WRE_R2(Real_Freq, sketch, top_k):
	# R2: https://zh.wikipedia.org/wiki/%E5%86%B3%E5%AE%9A%E7%B3%BB%E6%95%B0
	ARE, AAE, ASE, WRE = 0, 0, 0, 0
	S_tot, S_res, = 0, 0

	all_ground = sorted(Real_Freq.items(), key=lambda x: x[1], reverse=True)
	ground = all_ground[:top_k]
	vals = [g[1] for g in ground]
	mean_val = sum(vals)/len(vals)
	for i in range(len(ground)):
		key, val = ground[i]
		est_val = sketch.query(key)
		dist = abs(val - est_val)
		ARE += dist/val
		AAE += dist
		ASE += dist**2
		WRE += val

		S_tot += (val - mean_val)**2
		S_res += (val - est_val)**2

	WRE = AAE / WRE
	ARE /= len(ground)
	AAE /= len(ground)
	ASE /= len(ground)
	R2 = 1 - S_res/S_tot

	return ARE, AAE, ASE, WRE, R2

def Cal_PRED_PRE_REC_F1_ACC(Real_Freq, top_k, flowids, fea_y):
	# Real_Freq.items(): key, val
	ground = sorted(Real_Freq.items(), key=lambda x: x[1], reverse=True)
	ground_id = [x[0] for x in ground]
	top_set = set(ground_id[:top_k])
	y_true = list(
		map(lambda x: 1 if x in top_set else 0, flowids))
	y_pred = fea_y

	PRE, REC, F1, _ = precision_recall_fscore_support(y_true, y_pred, \
		pos_label=1, average='weighted', warn_for=())
	ACC = accuracy_score(y_true, y_pred)
	# if name == 'SK':
	# 	z = np.column_stack((y_true, y_pred))
	# 	np.savetxt('text.txt', z)
	return PRE, REC, F1, ACC


def Cal_PRE_REC_F1_ACC(Real_Freq, sketch, top_k):
	y_true = np.array([0 for _ in range(len(Real_Freq))])
	y_true[:top_k] = 1
	ground = sorted(Real_Freq.items(), key=lambda x: x[1], reverse=True)
	hh_set = set(sketch.get_heavy_hitters(top_k))

	y_pred = [0 for _ in range(len(ground))]
	for i in range(len(ground)):
		k, v = ground[i]
		y_pred[i] = 1 if k in hh_set else 0
	
	PRE, REC, F1, _ = precision_recall_fscore_support(y_true, y_pred, \
		pos_label=1, average='weighted', warn_for=())
	ACC = accuracy_score(y_true, y_pred)
	return PRE, REC, F1, ACC
