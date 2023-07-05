# -*- coding: utf-8 -*-
# @Author: xiegr
# @Date:   2020-01-13 17:35:28
# @Last Modified by:   xiegr
# @Last Modified time: 2020-07-09 12:13:59
from .Include import *
from OtherSketches.Hash import Hash

class Heavy(object):
	"""docstring for Heavy"""
	def __init__(self, BUCKETS_NUM=BUCKETS_NUM):
		super(Heavy, self).__init__()
		self.buckets = []
		self.BUCKETS_NUM = BUCKETS_NUM
		for _ in range(self.BUCKETS_NUM):
			self.buckets.append(Bucket())

		self.hash = Hash(BUCKETS_NUM).hash
		self.MAX_VALID_COUNTER = COUNTERS_PER_BUCKET-1

	def get_real_val(self, val):
		return val & 0x7FFFFFFF

	def check_match(self, fp, pos):
		for i in range(self.MAX_VALID_COUNTER):
			if self.buckets[pos].counter[i].key == fp:
				return i

		return -1

	def find_min(self, val, idx, pos):
		val = 0xFFFFFFFF
		idx = -1

		for i in range(self.MAX_VALID_COUNTER):
			if self.get_real_val(
				self.buckets[pos].counter[i].val) <= val:
				val = self.get_real_val(
					self.buckets[pos].counter[i].val)
				idx = i

		return val, idx

	def whether_swap(self, vote_negative, vote_positive):
		if vote_negative / vote_positive < LAMDA:
			return False
		return True

	def insert(self, key, swap_key, swap_val, f=1):
		# assert len(key) == KEY_LEN, 'key should be 4 bytes in heavy insert'

		fp = key

		hash_val = self.hash(str(key))
		pos = (hash_val) % self.BUCKETS_NUM

		matched = self.check_match(fp, pos)

		# find matched key in a specific counter
		if matched != -1:
			self.buckets[pos].counter[matched].val += f
			return CASE_2, swap_key, swap_val

		min_counter_val = 0xFFFFFFFF
		min_counter = -1
		min_counter_val, min_counter = self.find_min(
			min_counter_val, min_counter, pos)

		# empty counter
		if min_counter_val == 0:
			self.buckets[pos].counter[min_counter].key = fp
			self.buckets[pos].counter[min_counter].val = f  # highest bit flag is 0 because f is 0x1
			return CASE_1, swap_key, swap_val

		guard_val = self.buckets[pos].counter[self.MAX_VALID_COUNTER].val
		guard_val += 1

		if not self.whether_swap(guard_val, min_counter_val):
			self.buckets[pos].counter[self.MAX_VALID_COUNTER].val = guard_val
			return CASE_3, swap_key, swap_val

		swap_key = self.buckets[pos].counter[min_counter].key
		swap_val = self.get_real_val(self.buckets[pos].counter[min_counter].val)

		self.buckets[pos].counter[self.MAX_VALID_COUNTER].val = 0

		self.buckets[pos].counter[min_counter].key = fp
		self.buckets[pos].counter[min_counter].val = 0x80000001
		return CASE_4, swap_key, swap_val

	def query(self, key):
		# assert len(key) == KEY_LEN, 'key should be 4 bytes in heavy query'
		
		fp = key
		hash_val = self.hash(str(key))
		pos = (hash_val) % self.BUCKETS_NUM

		matched = self.check_match(fp, pos)

		if matched != -1:
			return self.buckets[pos].counter[matched].val
		return 0

	def get_heavy_hitters(self):
		result = []
		for row in self.buckets:
			for i in range(self.MAX_VALID_COUNTER):
					result.append(row.counter[i])

		return result
