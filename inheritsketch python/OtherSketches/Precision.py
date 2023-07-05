# -*- coding: utf-8 -*-
# @Author: xgr19
# @Date:   2022-05-12 16:03:42
# @Last Modified by:   xgr19
# @Last Modified time: 2022-05-19 11:44:26
from OtherSketches.HashPipe import HashPipe
import random

random.seed(10)

class PRECISION(HashPipe):
	def insert(self, ip, val=1):
		min_ = 0xFFFFFFFF
		pos = None
		ktable = None

		for i in range(0, self.d):
			idx = self.hashes[i](ip)%self.table_len
			if self.tables[i][idx].flowid == None:
				self.tables[i][idx].flowid = ip
				self.tables[i][idx].cnt = val
				return
			elif self.tables[i][idx].flowid == ip:
				self.tables[i][idx].increase(val)
				return
			elif self.tables[i][idx].cnt < min_:
				min_ = self.tables[i][idx].cnt
				pos = idx
				ktable = i

		if random.random() <= min(1/min_, 0.01):
			self.resub += 1
			self.tables[ktable][pos].flowid = ip
			self.tables[ktable][pos].flowid = val

	def query(self, ip):
		cnt = 0
		for i in range(self.d):
			idx = self.hashes[i](ip)%self.table_len
			if self.tables[i][idx].flowid == ip:
				cnt = self.tables[i][idx].cnt
		return cnt