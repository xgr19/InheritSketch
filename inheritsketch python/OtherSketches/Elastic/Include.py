# -*- coding: utf-8 -*-
# @Author: xiegr
# @Date:   2020-01-13 17:16:43
# @Last Modified by:   xiegr
# @Last Modified time: 2020-07-07 16:38:08

# heavy
HEAVY_MEM_IN_BYTES = 8*1024
COUNTERS_PER_BUCKET = 8
# 4 bytes for count, 2 bytes for flowID, per CounterWithKey in heavy
BUCKETS_NUM = HEAVY_MEM_IN_BYTES//(COUNTERS_PER_BUCKET*8)

CASE_1 = 1  # insert into an empty counter
CASE_2 = 2  # find matched key in a specific counter
CASE_3 = 3  # no matched key, vote^-/vote^+ < lamda (8)
CASE_4 = 4  # no matched key, vote^-/vote^+ >= lamda
LAMDA = 8

class CounterWithKey(object):
	"""docstring for CounterWithKey"""
	def __init__(self):
		super(CounterWithKey, self).__init__()
		self.key = b'\x00\x00\x00\x00'
		self.val = 0

class Bucket(object):
	"""docstring for Bucket"""
	def __init__(self):
		super(Bucket, self).__init__()
		self.counter = []
		for _ in range(COUNTERS_PER_BUCKET):
			self.counter.append(CounterWithKey())

# slight
SLIGHT_MEM_IN_BYTES = 56*1024
COUNTERS_NUM = SLIGHT_MEM_IN_BYTES

class Counter(object):
	"""docstring for Counter"""
	def __init__(self):
		super(Counter, self).__init__()
		self.val = 0
		
