# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-04-12 12:19:31
# @Last Modified by:   xiegr
# @Last Modified time: 2022-05-07 16:29:29
import mmh3
from zlib import crc32
from random import randint

# 32-bits hash
class Hash(object):
	def __init__(self, seed):
		# 固定 hash seed，防止不同次实验结果波动过大
		# self.seed = randint(1, 0xFFFFFFFF)
		self.seed = seed

	def hash(self, key):
		# return mmh3.hash(key, self.seed) & 0xFFFFFFFF
		return crc32(key.encode('utf8'), self.seed) & 0xFFFFFFFF