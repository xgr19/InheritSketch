# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-02-22 21:46:52
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-11 21:49:46
from array import array
from OtherSketches.CountMin import CountMin
from OtherSketches.Hash import Hash
from math import ceil

class Count(CountMin):
	def __init__(self, mem, d=2, cnt_bytes=4, max_val=0xFFFF, \
		min_val=-0xFFFF):
		super(Count, self).__init__(mem, d, cnt_bytes)
		self.min_val = min_val
		self.counts = [[0 for _ in range(self.w)] for _ in range(self.d)]
		self.sign = [Hash(i).hash for i in range(d)]

	def get_row_constant(self, a, row):
		constants = [-1, 1]
		return constants[self.sign[row](a)%2]

	def insert(self, a, val=1):
		for row, col in zip(list(range(self.d)), self.get_columns(a)):
			tmp = self.counts[row][col] + (val*self.get_row_constant(a, row))
			if tmp < self.min_val:
				tmp = self.min_val
			elif tmp > self.max_val:
				tmp = self.max_val

			self.counts[row][col] = tmp

	def swap(self, a, val):
		old = self.query(a)
		val = max(val-old, 0)
		self.insert(a, val)
	
	def query(self, a):
		candidates = [
			self.counts[row][col]*self.get_row_constant(a, row)
			for row, col in zip(list(range(self.d)), self.get_columns(a))
		]
		candidates.sort()

		mid = ceil(len(candidates)/2)
		return candidates[mid]

	def get_heavy_hitters(self, thresh):
		return []



