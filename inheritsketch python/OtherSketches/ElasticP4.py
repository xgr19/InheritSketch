# -*- coding: utf-8 -*-
# @Author: xgr19
# @Date:   2022-05-13 12:53:29
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-13 18:36:44
from OtherSketches.CountMin import CountMin
from OtherSketches.Hash import Hash

ELAMBDA = 5

class MainCounter(object):
	"""docstring for MainCounter"""
	def __init__(self, max_val):
		super(MainCounter, self).__init__()
		self.max_val = max_val
		self.flowid = None  # 8B
		self.tot_cnt = 0    # 4B
		self.pos_cnt = 0    # 4B

	def increase_tot(self, val):
		self.tot_cnt = min(self.tot_cnt+val, self.max_val)

	def increase_pos(self, val):
		self.pos_cnt = min(self.pos_cnt+val, self.max_val)

	def div(self):
		return self.tot_cnt >> ELAMBDA


class ElasticP4(object):
	"""docstring for Elastic"""
	def __init__(self, mem1, mem2, d=4, \
		main_maxval=0xFFFFFFFF, main_bytes=8+4+4):
		self.light = CountMin(mem=mem2, d=1, cnt_bytes=1)
		self.main_maxval = main_maxval
		self.resub = 0
		self.d = d
		self.main_hashes = [Hash(i).hash for i in range(d)]

		len_main = mem1//main_bytes//d
		self.heavy = [[] for _ in range(d)]

		for k in range(0,d):
			self.heavy[k] = \
			[
				MainCounter(self.main_maxval) for _ in range(len_main)
			]

	def insert(self, ip, val=1):
		carry_Counter = MainCounter(self.main_maxval)
		carry_Counter.flowid = ip
		carry_Counter.pos_cnt = val

		for i in range(self.d):
			idx = self.main_hashes[i](carry_Counter.flowid)%len(self.heavy[i])
			self.heavy[i][idx].increase_tot(carry_Counter.pos_cnt)
			
			if self.heavy[i][idx].flowid == None or \
			self.heavy[i][idx].flowid == carry_Counter.flowid:
				self.heavy[i][idx].flowid = carry_Counter.flowid
				self.heavy[i][idx].increase_pos(carry_Counter.pos_cnt)
				return

			tot_div = self.heavy[i][idx].div()
			if tot_div >= self.heavy[i][idx].pos_cnt:
				tmp = self.heavy[i][idx].flowid
				self.heavy[i][idx].flowid = carry_Counter.flowid
				carry_Counter.flowid = tmp

				tmp = self.heavy[i][idx].pos_cnt
				self.heavy[i][idx].increase_pos(carry_Counter.pos_cnt)
				carry_Counter.pos_cnt = tmp

		self.light.insert(carry_Counter.flowid, carry_Counter.pos_cnt)

	def query(self, ip):
		cnt = 0
		for i in range(self.d):
			idx = self.main_hashes[i](ip)%len(self.heavy[i])
			if self.heavy[i][idx].flowid == ip:
				cnt += self.heavy[i][idx].pos_cnt
		
		return cnt+self.light.query(ip)


	def get_heavy_hitters(self, top_k):
		import operator
		key_val = dict()
		for row in self.heavy:
			for col in row:
				key_val[col.flowid] = key_val.get(col.flowid, 0) + col.pos_cnt

		all_counters = [(k, v) for k,v in key_val.items()]
		result = sorted(all_counters, key=lambda tup: tup[1])
		return set([c[0] for c in result[-top_k:]])

		
		