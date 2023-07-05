# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-02-22 21:46:52
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-18 15:42:25
from array import array
from OtherSketches.Hash import Hash

class CountMin(object):
	def __init__(self, mem, d=2, cnt_bytes=4):
		# w: counter width
		# d: hash depth
		self.w = (mem//d)//cnt_bytes
		self.d = d
		self.max_val = (0x1 << (cnt_bytes*8))-1
		self.counts = [[0 for _ in range(self.w)] for _ in range(self.d)]
		self.hashes = [Hash(i).hash for i in range(self.d)]
		self.resub = 0
		
	def get_columns(self, a):
		for h in self.hashes:
			yield h(a) % self.w
		
	def insert(self, a, val=1):
		for row, col in zip(self.counts, self.get_columns(a)):
			row[col] = min(row[col]+val, self.max_val)

	def swap(self, a, val):
		for row, col in zip(self.counts, self.get_columns(a)):
			row[col] = min(max(row[col], val), self.max_val)
	
	def query(self, a):
		return min(row[col] for row, col in zip(self.counts, self.get_columns(a)))

	def get_heavy_hitters(self, thresh):
		return []

	def get_primary_info(self, name='CM'):
		return None


