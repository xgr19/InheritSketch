# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-05-19 22:09:06
# @Last Modified by:   xiegr
# @Last Modified time: 2023-07-05 19:02:20
from OtherSketches.CountMin import CountMin
from OtherSketches.Hash import Hash
import numpy as np
import sys

THRESH = 50

class Predictor(object):
	"""docstring for Predictor"""
	def __init__(self):
		super(Predictor, self).__init__()
		self.cls0 = None
		self.trained = False

	def naive(self, X):
		return np.array([0]*len(X), dtype=int)
		

class FakeDT(Predictor):
	"""docstring for FakeDT"""
	def __init__(self):
		super(FakeDT, self).__init__()

	def predict(self, X):
		if self.cls0 is None:
			return self.naive(X)
		else:
			flowids = X
			return np.array(
				list(
						map(lambda x: 1 if x in self.cls0 else 0, flowids)
					)
				, dtype=int)

	def train(self, X, Y, name='FK'):
		if self.trained:
			return
		clf = set()
		for x, y in zip(X, Y):
			# if y == 1:
			clf.add(x)

		self.cls0 = clf
		# self.trained = True

	def get_heavy_hitters(self, top_k):
		return self.cls0
		

class IDFeaCounter(object):
	def __init__(self, id_bytes, fea_bytes, cnt_bytes):
		super(IDFeaCounter, self).__init__()
		self.id = None
		self.cnt = 0
		self.features = None
		self.max_val = (0x1 << (cnt_bytes*8))-1

	def increase(self, val=1):
		self.cnt = min(self.cnt+val, self.max_val)



class DTSketch(object):
	def __init__(self, primary_mem, cm_mem, multi_hash=3,\
		id_bytes=8, fea_bytes=0, cnt_bytes=4):
		# new id: src+dst ip (8B)
		# id: 5 tuple (4+4+2+2+1=13B), features: ip.len, ip.flags, ttl, tcp.win (2+1+1+2=6B)
		self.w = (primary_mem//multi_hash)//(id_bytes+cnt_bytes+fea_bytes)
		self.d = multi_hash
		self.primary = [IDFeaCounter(id_bytes, fea_bytes, cnt_bytes) for _ in range(self.w*self.d)]
		self.primary_hashes = [Hash(i).hash for i in range(self.d)]
		self.assistant = CountMin(mem=cm_mem, d=1, cnt_bytes=1)
		self.resub = 0
		

	def insert(self, flowid, features=None, cls=0, val=1):
		min_counter = self.primary[self.primary_hashes[0](flowid)%self.w]

		for i in range(self.d):
			c = self.primary[i*self.w+(self.primary_hashes[i](flowid)%self.w)]
			if c.id is None and cls == 1:
				# empty, id equal but cnt=0
				c.id = flowid
				c.features = features
				c.increase(val)
				return
			elif c.id == flowid:
				# update features
				c.features = features
				c.increase(val)
				return
			elif c.cnt < min_counter.cnt:
				min_counter = c

		# a flow can not insert into primary
		cnt = self.assistant.query(flowid)+val
		if cnt > max(min_counter.cnt, THRESH):
			self.resub += 1
			if min_counter.id == None:
				min_counter.id = flowid
				min_counter.features = features
				min_counter.cnt = cnt
			else:
				self.swap(flowid, features, cnt, min_counter)
		else:
			self.assistant.insert(flowid, val)

	def swap(self, flowid, features, cnt, min_counter):
		# self.assistant.insert(min_counter.id, min_counter.cnt)
		self.assistant.swap(min_counter.id, min_counter.cnt)
		min_counter.id = flowid
		min_counter.features = features
		min_counter.cnt = cnt

	def query(self, flowid):
		for i in range(self.d):
			c = self.primary[i*self.w+(self.primary_hashes[i](flowid)%self.w)]
			if c.id == flowid:
				return c.cnt
		return self.assistant.query(flowid)

	def get_heavy_hitters(self, top_k):
		info = sorted(self.primary, key=lambda x: x.cnt, reverse=True)
		result = [c.id for c in info[:top_k]]
		return result

	def get_primary_info(self, name):
		info = sorted(self.primary, key=lambda x: x.cnt, reverse=True)
		print('****** primary info %s *****'%name)
		print('len: %d'%len(info))
		print('top1 cnt= %d, '%(info[1].cnt),end='')
		# print('top100 cnt= %d, '%(info[100].cnt),end='')
		# print('top300 cnt= %d, '%(info[300].cnt),end='')
		print('top500 cnt= %d, '%(info[500].cnt),end='')
		print('top800 cnt= %d, '%(info[800].cnt if len(info) > 800 else info[-1].cnt),end='')
		print('top1000 cnt= %d'%(info[1000].cnt if len(info) > 1000 else info[-1].cnt))

	def features_for_FK(self, top_k):
		info = sorted(self.primary, key=lambda x: x.cnt, reverse=True)
		X, Y = [], []
		for i in range(len(info)):
			if info[i].id is None:
				continue

			x = info[i].id
			X.append(x)
			Y.append(1)
		return np.array(X), np.array(Y)

if __name__ == '__main__':
	sk = DTSketch(primary_mem=8*1024, cm_mem=56*1024)
	dict1 = {'1.2.3.4': 20, '4.3.2.1': 5}
	dict2 = {'1.2.3.4': 2, '4.3.2.1': 100}

	sk.insert('1.2.3.4', val=dict1['1.2.3.4'])
	sk.insert('4.3.2.1', val=dict2['4.3.2.1'])
	sk.insert('1.2.3.4', val=dict2['1.2.3.4'])
	sk.insert('4.3.2.1', val=dict1['4.3.2.1'])

	for flowid in ['1.2.3.4', '4.3.2.1']:
		print(sk.query(flowid))