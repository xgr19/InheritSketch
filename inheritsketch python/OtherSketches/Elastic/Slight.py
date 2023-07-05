# -*- coding: utf-8 -*-
# @Author: xiegr
# @Date:   2020-01-13 17:00:57
# @Last Modified by:   xiegr
# @Last Modified time: 2020-07-09 12:14:13
from .Include import *
from OtherSketches.Hash import Hash

class Slight(object):
	"""docstring for Slight"""
	def __init__(self, COUNTERS_NUM=COUNTERS_NUM):
		super(Slight, self).__init__()
		self.counters = []
		self.COUNTERS_NUM = COUNTERS_NUM
		for _ in range(self.COUNTERS_NUM):
			self.counters.append(Counter())

		self.hash = Hash(COUNTERS_NUM).hash

	def insert(self, key, f=1):
		# assert len(key) == KEY_LEN, 'key should be 4 bytes in slight insert'
		
		hash_val = self.hash(str(key))
		pos = (hash_val) % self.COUNTERS_NUM

		old_val = self.counters[pos].val
		new_val = old_val + f

		new_val = min(new_val, 0xFF)
		self.counters[pos].val = new_val

	def query(self, key):
		# assert len(key) == KEY_LEN, 'key should be 4 bytes in slight query'
		
		hash_val = self.hash(str(key))
		pos = (hash_val) % self.COUNTERS_NUM

		return self.counters[pos].val
		