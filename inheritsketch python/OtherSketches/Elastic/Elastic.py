# -*- coding: utf-8 -*-
# @Author: xiegr
# @Date:   2020-01-13 18:36:40
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-11 21:53:12
from . import Slight, Heavy
from .Include import *
from OtherSketches.Hash import Hash

class Elastic(object):
	"""docstring for Elastic"""
	def __init__(self, mem1, mem2, cnt_bytes=8+4):
		super(Elastic, self).__init__()
												# 8 for id, 4 for cnt
		BUCKETS_NUM = (mem1)//(COUNTERS_PER_BUCKET*cnt_bytes)
		COUNTERS_NUM = mem2
		self.heavy_part = Heavy.Heavy(BUCKETS_NUM)
		self.light_part = Slight.Slight(COUNTERS_NUM)
		self.resub = 0

	def insert(self, key, f=1):
		swap_key = b'\x00\x00\x00\x01'
		swap_val = 0

		result, swap_key, swap_val = \
		self.heavy_part.insert(key, swap_key, swap_val, f)

		if result == CASE_1 or result == CASE_2:
			# empty counter in heavy bucket or find key in heavy
			return
		elif result == CASE_4:
			# no matched key, vote^-/vote^+ >= lamda 8, swap
			self.light_part.insert(swap_key, swap_val)
			return
		elif result == CASE_3:
			# no matched key, vote^-/vote^+ < lamda, no swap
			self.light_part.insert(key, f)
			return
		else:
			print('error return value when insert into heavy!')
			exit(0)

	def query(self, key):
		heavy_result = self.heavy_part.query(key)
		if heavy_result == 0 or heavy_result & 0x80000000:
			light_result = self.light_part.query(key)
			return self.heavy_part.get_real_val(heavy_result) + light_result
		return heavy_result # highest bit is not 1

	def get_heavy_hitters(self, top_k):
		import operator
		all_counters = self.heavy_part.get_heavy_hitters()
		result = sorted(all_counters, key=operator.attrgetter('val'))
		return set([c.key for c in result[-top_k:]])

		