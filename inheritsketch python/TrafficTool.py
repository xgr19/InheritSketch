# -*- coding: utf-8 -*-
# @Author: xieguorui
# @Date:   2020-05-01 00:55:16
# @Last Modified by:   xiegr
# @Last Modified time: 2023-07-05 18:50:26
import dpkt
import numpy as np
from multiprocessing import Pool
import os, time, random
from time import time as Time
import time

def get_traffic_info(Real_Freq, npy_name):
	info = sorted(Real_Freq.items(), key=lambda x: x[1], reverse=True)
	steps = [1, 500, 800, 1000, -1]
	cdf = []
	for s in steps:
		if s == -1:
			for i in range(len(info)):
				if info[i][1] <= 5:
					break
			cdf.append((len(info)-i)/len(info))
		else:	
			cdf.append((len(info)-s)/len(info))

	print('****** Traffic info *****')
	print('len: %d'%len(info))
	for i in range(len(steps)):
		print('top%d (cnt=%d, cdf=%f) '%(
			steps[i], info[steps[i] if len(info) > steps[i] else -1][1], cdf[i]))

	with open('cdfs/'+npy_name[npy_name.rfind('/')+1:]+'.cdf.txt', 'w') as f:
		info_asc = sorted(Real_Freq.items(), key=lambda x: x[1])
		last = 1
		for i in range(0,len(info_asc)):
			if info_asc[i][1] <= last:
				continue
			else:
				f.write('%d 1 %f\n'%(
					last, (i+1)/len(info_asc)
					))
				last = info_asc[i][1]

def extract_feature(p):
	features = ['src', 'dst', 'p', 'sport', 'dport', \
	'mf', 'df', 'ttl', 'win', 'len']
	tmp = []
	for i in range(len(features)):
		if features[i] == 'src' or features[i] == 'dst':
			ips = list(map(int, getattr(p, features[i])))
			tmp.extend([ips[0],ips[1],ips[2],ips[3]])
		elif features[i] == 'sport' or features[i] == 'dport':
			if isinstance(p.data, dpkt.udp.UDP) or \
			isinstance(p.data, dpkt.tcp.TCP):
				port = getattr(p.data, features[i]) 
			else:
				port = 0
			tmp.append(port)
		elif features[i] == 'win':
			win = getattr(p.data, features[i]) if \
			isinstance(p.data, dpkt.tcp.TCP) else 0
			tmp.append(win)
		else:
			tmp.append(getattr(p, features[i]))
	return tmp

def read_all(pcap_name):
	pcap_reader = dpkt.pcap.Reader(open(pcap_name, 'rb'))
	cnt = 0
	for _, buff in pcap_reader:
		# for循环的退出不会影响文件对象内秉的__next__属性，
		# 除非这个文件对象被重置seek(0), f.seek(0)
		if pcap_reader.datalink() == dpkt.pcap.DLT_RAW \
		or pcap_reader.datalink() == 101:
		# https://www.tcpdump.org/linktypes.html
			if buff[0] >> 4 == 4:
				# Raw IP; the packet begins with an IPv4 or IPv6 header, \
				# with the "version" field of the header indicating \
				# whether it's an IPv4 or IPv6 header.
				try:
					pkt_ip = dpkt.ip.IP(buff)
				except:
					continue
				yield extract_feature(pkt_ip)
		elif pcap_reader.datalink() == dpkt.pcap.DLT_EN10MB:
			try:
				eth = dpkt.ethernet.Ethernet(buff)
			except:
				continue
			if isinstance(eth.data, dpkt.ip.IP):
				yield extract_feature(eth.data)
		else:
			print('datalink/linktype ', \
				pcap_reader.datalink(), ' is unknown!')
			break

		cnt += 1
		# if cnt == 100000:
		# 	break

def write_npy(name, idx):
	t0 = Time()
	traffic = []
	for i in read_all(name):
		traffic.append(i)
	traffic = np.array(traffic, dtype=int)
	np.save(name.replace('.pcap', '.npy') if '.pcap' in name else name+'.npy', traffic)
	print('the %dth finish, time: %.2f'%(idx, (Time()-t0)/60))


def write_flowid(npy_name, idx):
	t0 = Time()
	# ['src0', 'src1', 'src2', 'src3', 'dst0', 'dst1', 'dst2', 'dst3', \
						# 'p', 'sport', 'dport', 'mf', 'df', 'ttl', 'win', 'len']
	traffic = np.load(npy_name)
	flowids = np.array(
		list(
			map(lambda x: '.'.join(list(map(str, x))), traffic[:,:8])
		)
	)
	np.save(npy_name.replace('.npy', '.flowid'), flowids)
	print(traffic[0])
	print(flowids[0])
	print('the %dth finish, time: %.2f'%(idx, (Time()-t0)/60))


def process_caida_univ(name, root, start=0, end=20, step=1, prefix='dirB'):
	# dirA, step=4
	localtime = time.asctime(time.localtime(Time()))
	print('\n', localtime, prefix)
	for i in range(start, end, step):
		p = Pool(step)
		for j in range(0, step):
			a = p.apply_async(write_npy, args=(root%prefix+name%(i+j), i+j,))
		p.close()
		p.join()
		print(a.get())
		print('npy subprocesses done.')

	name = name+'.npy' if '.pcap' not in name else name.replace('.pcap', '.npy')
	for i in range(start, end, step):
		p = Pool(step)
		for j in range(0, step):
			a = p.apply_async(write_flowid, args=(root%prefix+name%(i+j), i+j,))
		p.close()
		p.join()
		print(a.get())
		print('flowid subprocesses done.')


def merge_univ1(start, end, root='/data/xgr/sketch_data/imc_univ1/', \
	prefix='univ1'):

	def combine_pcaps(start, end, root='/data/xgr/sketch_data/imc_univ1/', \
		prefix='univ1'):
		pcaps = [root+'%s_pt%d'%(prefix, i) for i in range(start, end)]
		pcap_reader = dpkt.pcap.Reader(open(pcaps[0], 'rb'))
		pcap_writer = dpkt.pcap.Writer(open(root+prefix+'_all_0.pcap','wb'), linktype=pcap_reader.datalink())

		for name in pcaps:
			pcap_reader = dpkt.pcap.Reader(open(name, 'rb'))
			for ts,buf in pcap_reader:
				pcap_writer.writepkt(buf,ts)

		pcap_writer.close()

	localtime = time.asctime(time.localtime(Time()))
	print('\n', localtime, prefix)

	combine_pcaps(start, end, root, prefix)
	name = '_all_0.pcap'
	write_npy(root+prefix+name, 0)
	print('write npy ends', prefix)

	name = '_all_0.npy'
	write_flowid(root+prefix+name, 0)


if __name__ == '__main__':
	# 30个，min0-min29
	prefix = 'dirA'
	name = 'equinix-nyc.'+prefix+'.20180315-13%02d00.UTC.anon.pcap'
	root = '/data/xgr/traces/caida%s/'
	process_caida_univ(name, root, start=0, end=30, step=4, prefix=prefix)

	prefix = 'cernet'
	name = '20201227_14%02d00_ingress.pcap'
	root = '/data/xgr/traces/%s/'
	process_caida_univ(name, root, start=0, end=30, step=4, prefix=prefix)

	# prefix = 'HGC'
	# name = '200904100%02d.pcap'
	# root = '/data/xgr/traces/%s/'
	# process_caida_univ(name, root, start=1, end=28, step=4, prefix=prefix)

	prefix = 'dirA'
	name = 'equinix-nyc.'+prefix+'.20190117-13%02d00.UTC.anon.pcap'
	root = '/data/xgr/sketch_data/caida_%s/'
	process_caida_univ(name, root, start=20, end=30, step=4, prefix=prefix)

	# prefix = 'dirB'
	# name = 'equinix-nyc.'+prefix+'.20190117-13%02d00.UTC.anon.pcap'
	# root = '/data/xgr/sketch_data/caida_%s/'
	# process_caida_univ(name, root, start=0, end=30, step=1, prefix=prefix)

	# # 20个，1~20
	# prefix = 'univ1'
	# name = prefix+'_pt%d'
	# root = '/data/xgr/sketch_data/imc_%s/'
	# process_caida_univ(name, root, start=1, end=21, step=4, prefix=prefix)

	# prefix = 'univ1'
	# root = '/data/xgr/sketch_data/imc_%s/'%prefix
	# merge_univ1(start=1, end=21, root=root, prefix=prefix)

	# # 7个， 0~7
	# prefix = 'univ2'
	# name = prefix+'_pt%d'
	# root = '/data/xgr/sketch_data/imc_%s/'
	# process_caida_univ(name, root, start=0, end=8, step=4, prefix=prefix)
