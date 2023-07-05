# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-04-12 12:40:11
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-11 18:09:25
from OtherSketches.Hash import Hash

# 4 Bytes id, 4 Bytes cnt, 2Bytes ass
class MainCounter(object):
	"""docstring for MainCounter"""
	def __init__(self, max_val):
		super(MainCounter, self).__init__()
		self.max_val = max_val
		self.flowid = None
		self.cnt = 0
	def increase(self, val):
		self.cnt = min(self.cnt+val, self.max_val)
		

class AssCounter(object):
	"""docstring for AssCounter"""
	def __init__(self, max_val):
		super(AssCounter, self).__init__()
		self.max_val = max_val
		self.digest = None
		self.cnt = 0
	def increase(self, val):
		self.cnt = min(self.cnt+1, self.max_val)	


class HashFlow(object):
	"""docstring for HashFlow"""
	def __init__(self, mem1, mem2, d=3, \
		main_maxval=0xFFFFFFFF, main_bytes=8+4, \
		ass_maxval=0xFF, ass_bytes=2, \
		ass_digest=0xFF, alpha=0.7):
		# 8 Bytes id, 4 Bytes cnt, 2 Bytes ass
		super(HashFlow, self).__init__()
		self.main_maxval = main_maxval
		self.ass_maxval = ass_maxval
		self.ass_digest = ass_digest
		self.resub = 0

		self.d = d
		self.main_hashes = [Hash(i).hash for i in range(d)]
		self.digest_hash = Hash(d).hash
		self.ass_hash = Hash(d+1).hash

		len_main = (mem1)//main_bytes
		self.multi_main_table = [[] for _ in range(d)]

		for k in range(1,d+1):
			klen = int(pow(alpha, k-1)*(1-alpha)*len_main/(1-pow(alpha, d)))
			self.multi_main_table[k-1] = \
			[
				MainCounter(self.main_maxval) for _ in range(klen)
			]

		self.len_ass = (mem2)//ass_bytes
		self.ass_table = [
			AssCounter(self.ass_maxval) for _ in range(self.len_ass)
		]


	def insert(self, ip, val=1):
		min_ = 0xFFFFFFFF
		pos = None
		ktable = None

		for i in range(self.d):
			idx = self.main_hashes[i](ip)%len(self.multi_main_table[i])
			if self.multi_main_table[i][idx].flowid == None:
				self.multi_main_table[i][idx].flowid = ip
				self.multi_main_table[i][idx].cnt = val
				return
			elif self.multi_main_table[i][idx].flowid == ip:
				self.multi_main_table[i][idx].increase(val)
				return
			elif self.multi_main_table[i][idx].cnt < min_:
				min_ = self.multi_main_table[i][idx].cnt
				pos = idx
				ktable = self.multi_main_table[i]

		idx = self.ass_hash(ip)%self.len_ass
		digest = self.digest_hash(ip)&self.ass_digest
		if self.ass_table[idx].cnt == 0 or \
		self.ass_table[idx].digest != digest:
			# remove the old flow, under estimate
			self.ass_table[idx].digest = digest
			self.ass_table[idx].cnt = 1
		elif self.ass_table[idx].cnt < min_:
			self.ass_table[idx].increase(val)
		else:
			self.resub += 1
			ktable[pos].flowid = ip
			ktable[pos].cnt = min(self.ass_table[idx].cnt+1, \
				self.main_maxval)

	def query(self, ip):
		for i in range(self.d):
			idx = self.main_hashes[i](ip)%len(self.multi_main_table[i])
			if self.multi_main_table[i][idx].flowid == ip:
				return self.multi_main_table[i][idx].cnt

		idx = self.ass_hash(ip)%self.len_ass
		digest = self.digest_hash(ip)&self.ass_digest
		if self.ass_table[idx].digest == digest:
			return self.ass_table[idx].cnt

		return 0

	def get_heavy_hitters(self, top_k):
		import operator
		all_counters = []
		for row in self.multi_main_table:
			for col in row:
				all_counters.append(col)

		result = sorted(all_counters, key=operator.attrgetter('cnt'))
		return set([c.flowid for c in result[-top_k:]])

if __name__ == '__main__':
	HF = HashFlow(len_main=2, len_ass=4)
	HF.insert('1')
	HF.insert('1')
	print(HF.query('1'))


		