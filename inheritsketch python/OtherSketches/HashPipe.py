# -*- coding: utf-8 -*-
# @Author: xiegr
# @Date:   2020-07-05 17:17:07
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-12 12:46:32
from OtherSketches.Hash import Hash

# 4 Bytes id, 4 Bytes cnt, 2Bytes ass
class MainCounter(object):
	"""docstring for MainCounter"""
	def __init__(self, max_val):
		super(MainCounter, self).__init__()
		self.max_val = max_val
		self.flowid = None
		self.cnt = 0
	def increase(self, val=1):
		self.cnt = min(self.cnt+val, self.max_val)


class HashPipe(object):
	"""docstring for HashPipe"""
	def __init__(self, mem1, mem2, d=6, \
		maxval=0xFFFFFFFF, cnt_bytes=8+4):
		# src/dst ip = 8B, 4B cnt
		super(HashPipe, self).__init__()
		self.maxval = maxval
		self.hashes = [Hash(i).hash for i in range(d)]
		self.d = d
		self.resub = 0

		self.table_len = (mem1+mem2)//cnt_bytes//d
		self.tables = [
			[MainCounter(self.maxval) for _ in range(self.table_len)] for _ in range(d)
		]

	def insert(self, ip, val=1):
		idx = self.hashes[0](ip)%self.table_len
		if self.tables[0][idx].flowid == ip:
			self.tables[0][idx].increase(val)
			return
		elif self.tables[0][idx].flowid == None:
			self.tables[0][idx].flowid = ip
			self.tables[0][idx].cnt = val
			return
		else:
			carry_Counter = MainCounter(self.maxval)
			carry_Counter.flowid = self.tables[0][idx].flowid
			carry_Counter.cnt = self.tables[0][idx].cnt

			self.tables[0][idx].flowid = ip
			self.tables[0][idx].cnt = 1

		for i in range(1, self.d):
			idx = self.hashes[i](carry_Counter.flowid)%self.table_len
			if self.tables[i][idx].flowid == None:
				self.tables[i][idx].flowid = carry_Counter.flowid
				self.tables[i][idx].cnt = carry_Counter.cnt
				return
			elif self.tables[i][idx].flowid == carry_Counter.flowid:
				self.tables[i][idx].increase(carry_Counter.cnt)
				return
			elif self.tables[i][idx].cnt < carry_Counter.cnt:
				# swap
				tmp = MainCounter(self.maxval)
				tmp.flowid = self.tables[i][idx].flowid
				tmp.cnt = self.tables[i][idx].cnt

				self.tables[i][idx].flowid = carry_Counter.flowid
				self.tables[i][idx].cnt = carry_Counter.cnt

				carry_Counter.flowid = tmp.flowid
				carry_Counter.cnt = tmp.cnt

	def query(self, ip):
		cnt = 0
		for i in range(self.d):
			idx = self.hashes[i](ip)%len(self.tables[i])
			if self.tables[i][idx].flowid == ip:
				cnt += self.tables[i][idx].cnt
		return cnt

	def get_heavy_hitters(self, top_k):
		import operator
		key_val = dict()
		for row in self.tables:
			for col in row:
				key_val[col.flowid] = key_val.get(col.flowid, 0) + col.cnt

		all_counters = [(k, v) for k,v in key_val.items()]
		result = sorted(all_counters, key=lambda tup: tup[1])
		return set([c[0] for c in result[-top_k:]])