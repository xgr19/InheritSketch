# InheritSketch (ICDCS 2023)
**Paper title**: Efficient Flow Recording with InheritSketch on Programmable Switches

**Abstract (in brief)**: Several studies have been proposed to deploy the flow recording (i.e., flow size counting and sketching algorithms) on programmable switches for high-speed processing. In this paper, we propose InheritSketch for further improvement. InheritSketch utilizes a separation counting fashion, which is memory-efficient for compact switches. It accurately records the more valuable heavy hitters in the large key-value counters (i.e., the primary table), while only sketching non-heavy flows in the small sentinel table. With the recording ongoing, InheritSketch intelligently summarizes the historical recording experience as the basis for flow inheritance. That is, flows with the same IDs as the previous heavy hitters are regarded as new heavy hitters, being recorded in the primary table. To correct some incorrect inheritance, we also propose the flow rebellion, which promotes flows of large sizes but wrongly stored in the sentinel table to the primary table. InheritSketch is also helpful in applications like differentiated scheduling.

**Email**: Guorui Xie <xgr19@mails.tsinghua.edu.cn>

# Files
This repository has three folders:
1. inheritsketch python: maintains the P4 simulation codes to run inheritsketch (IS) on traces from CAIDA and CERNET.
2. inheritsketch P4 demo: the Tofino implementation of IS.
3. schedule simulation: runs flow scheduling simulation based on IS.

## inheritsketch python
0. obtain pcap files from CAIDA and CERNET. Typically, their pcap files are named by the capturing minute (e.g., 20201227_140000_ingress.pcap is one file from CERNET captured at 14:00).
1. run TrafficTool.py to obtain the .npy files that extract source ip+dest ip from pcaps.
2. run Main.py to get the IS results of flow size estimation (e.g., AAE, ARE) and heavy hitter (e.g., REC, F1).
3. run OtherMain.py to get results of HashFlow, PRECISION, ElasticSketch, etc.

All results are automatically written into csv files. Notably, IS is named DTSketch in the python files.

## inheritsketch P4 demo
The main file is psketch.p4 that consists of 3 primary tables (p1_table.p4, p2_table.p4, and p3_table.p4) and one assistant (sentinel ) table (a_table.p4)

## Schedule simulation
These codes are in go language, and are modified from [NetSys/ideal-simulator](https://github.com/NetSys/ideal-simulator).

We assume that the network is a big switch, and schedule flow in SRPT (ideal pfabirc),  FIFO, RAND (randomly), and PRIOR (priorities 0/1 from IS).

0. run TrafficTool.py to get cdf (cumulative distribution function) files of pcaps.
1. run main.go to obtain results in .txt files. In the simulation, flows of different sizes are generated according to cdf, then we assign them with arrival times based on Poisson distribution.
