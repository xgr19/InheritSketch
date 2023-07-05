import dpkt
import numpy as np
from multiprocessing import Pool
import os, time, random
from time import time as Time
import time
import struct
from scapy.all  import *
from multiprocessing import Pool

def genpkt(src, dst, sport, dport):
	# data = struct.pack( ' =BHI ',  0x12,  20,  1000)
	pkt = Ether(src='01:00:0c:cc:cc:cc', dst='00:11:22:33:44:55')/IP(src=src, dst=dst)/UDP(sport=sport,dport=dport)/"test"
	return pkt

def extract_feature(p):
	features = ['src', 'dst', 'sport', 'dport']
	tmp = []
	for i in range(len(features)):
		if features[i] == 'src' or features[i] == 'dst':
			ips = list(map(int, getattr(p, features[i])))
			tmp.append('%d.%d.%d.%d'%(ips[0],ips[1],ips[2],ips[3]))
		elif features[i] == 'sport' or features[i] == 'dport':
			if isinstance(p.data, dpkt.udp.UDP) or \
			isinstance(p.data, dpkt.tcp.TCP):
				port = getattr(p.data, features[i]) 
			else:
				port = 0
			tmp.append(port)
	return genpkt(src=tmp[0], dst=tmp[1], sport=tmp[2], dport=tmp[3])

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
		if cnt == 1000000:
			break


def write_pcaps(name, w):
	writer = PcapWriter(w)
	for i in read_all(name):
		writer.write(pkt=i)


if __name__ == '__main__':
	# caida 2018
	root = '/data/xgr/traces/caidadirA/'
	name = 'equinix-nyc.dirA.20180315-13%02d00.UTC.anon.pcap'
	# add process pool
	p = Pool(2)
	results = []
	results.append(
		p.apply_async(write_pcaps, args=(root+name%0, 'dirA20180.pcap')))
	results.append(
		p.apply_async(write_pcaps, args=(root+name%1, 'dirA20181.pcap')))
	p.close()
	p.join()
	
	for obj in results:
		print(obj)

	# caida 2019
	root = '/data/xgr/sketch_data/caida_dirA/'
	name = 'equinix-nyc.dirA.20190117-13%02d00.UTC.anon.pcap'
	# add process pool
	p = Pool(2)
	results = []
	results.append(
		p.apply_async(write_pcaps, args=(root+name%0, 'dirA20190.pcap')))
	results.append(
		p.apply_async(write_pcaps, args=(root+name%1, 'dirA20191.pcap')))
	p.close()
	p.join()
	
	for obj in results:
		print(obj)


	# cernet 2019
	root = '/data/xgr/traces/cernet/'
	name = '20201227_14%02d00_ingress.pcap'
	# add process pool
	p = Pool(2)
	results = []
	results.append(
		p.apply_async(write_pcaps, args=(root+name%0, 'cernet0.pcap')))
	results.append(
		p.apply_async(write_pcaps, args=(root+name%1, 'cernet1.pcap')))
	p.close()
	p.join()
	
	for obj in results:
		print(obj)

