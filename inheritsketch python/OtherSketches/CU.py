# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-02-22 21:46:52
# @Last Modified by:   xiegr
# @Last Modified time: 2020-07-07 16:31:34
from OtherSketches.CountMin import CountMin

class CU(CountMin):
	def insert(self, a, val=1):
		min_val = 0xFFFFFFFF
		min_row, min_col = None, None
		for row, col in zip(self.counts, self.get_columns(a)):
			if row[col] < min_val:
				min_val = row[col]
				min_row = row
				min_col = col

		# for row, col in zip(self.counts, self.get_columns(a)):
		# 	row[col] = max(row[col], min_val+val)
		min_row[min_col] = min(min_row[min_col]+val, self.max_val)



