package main

import (
	"bufio"
	"container/heap"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"math"
	"sort"
)

// generate flows
// read flow size CDF file and load for Poisson arrival

type CDF struct {
	values []uint
	distrs []float64
}

func readCDF(fn string) CDF {
	file, err := os.Open(fn)
	check(err)
	defer file.Close()

	vals := make([]uint, 16)
	cdfs := make([]float64, 16)
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		sp := strings.Split(scanner.Text(), " ")
		if sp[0][0] == '#' {
			continue
		}
		// structure of line: <flow's pkt sizes> <blah> <cdf>
		v, ok := strconv.ParseUint(sp[0], 10, 32)
		check(ok)
		c, ok := strconv.ParseFloat(sp[2], 64)
		check(ok)

		if v == 0 {
			panic("invalid cdf flow size")
		}

		vals = append(vals, uint(v)*1460)  // 每个包1460字节
		cdfs = append(cdfs, c)
	}

	return CDF{values: vals, distrs: cdfs}
}

func (cdf CDF) meanFlowSize() float64 {
	avg := 0.0
	lastCdf := 0.0
	for i := 0; i < len(cdf.values); i++ {
		avg += float64(cdf.values[i]) * (cdf.distrs[i] - lastCdf)
		lastCdf = cdf.distrs[i]
	}
	return avg
}

// 依概率生成一条流的packet size （cdf.values[i]）
func (cdf CDF) value() uint {
	rand := rand.Float64()
	for i := 0; i < len(cdf.values); i++ {
		if cdf.distrs[i] >= rand {
			if cdf.values[i] == 0 {
				panic("invalid flow size")
			}
			return cdf.values[i]
		}
	}

	panic("reached end of cdf function without value")
}

type FlowGenerator struct {
	load      float64
	bandwidth float64
	cdf       CDF
	numFlows  uint
}

func makeFlowGenerator(load float64, bw float64, cdfFile string, nf uint) FlowGenerator {
	return FlowGenerator{load: load, bandwidth: bw, cdf: readCDF(cdfFile), numFlows: nf}
}

func makeCreationEvent(f *Flow) *Event {
	if f.Start < 0 {
		panic("makeCreationEvent flow.FinishEvent < 0")
	}
	if f.Start < 1e6 {
		panic("makeCreationEvent flow.FinishEvent < 1e6")
	}
	return &Event{Time: f.Start, Flow: f, Type: FlowArrival, Cancelled: false}
}

func (fg FlowGenerator) makeFlows(exptype ScheduleType) EventQueue {
	// 单位时间内 1s 的平均流数目
	lambda := (fg.bandwidth * 1e9 * fg.load) / (fg.cdf.meanFlowSize() / 1460 * 1500 * 8)
	// lambda /= 143，每个host的平均流数目（1s）
	lambda /= (NUM_HOSTS - 1)

	creationQueue := make(EventQueue, 0) // make 返回实例，new 返回指针
	defer func() {
		creationQueue = nil
	}()
	sortedFlows := make(SortedFlows, fg.numFlows)
	defer func() {
		sortedFlows = nil
	}()

	// heap维护了按流到达时间小到大的排列
	heap.Init(&creationQueue)
	for i := 0; i < NUM_HOSTS; i++ {
		for j := 0; j < NUM_HOSTS; j++ {
			if i == j {
				continue
			}
			// 1s = 1e6 microsecond 微秒
			// 流间隔是指数分布，随机生成一个概率p，用累计概率函数求间隔x：1-e^(-lambdax)=p
			f := &Flow{Start: 1e6 + (-1 * math.Log(rand.Float64()) / lambda)*1e6, 
				Size: fg.cdf.value(), Source: uint8(i), Dest: uint8(j), 
				LastTime: 0, FinishEvent: nil, ExpType: exptype, 
				InterRack: rand.Intn(RACKS*RACKS) == LUCKY}
			heap.Push(&creationQueue, makeCreationEvent(f))
		}
	}

	idx := 0
	eventQueue := make(EventQueue, 0)
	// for condition {}
	for uint(len(eventQueue)) < fg.numFlows {
		ev := heap.Pop(&creationQueue).(*Event)
		// logger <- LogEvent{Time: 0, Type: LOG_FLOW_GEN, Flow: ev.Flow}
		eventQueue = append(eventQueue, makeArrivalEvent(ev.Flow))
		sortedFlows[idx] = ev.Flow
		idx = idx + 1

		// 上一个循环得到的流数目不一定==fg.numFlows，再产生新流
		nextTime := ev.Time + (-1 * math.Log(rand.Float64()) / lambda)*1e6
		f := &Flow{Start: nextTime, Size: fg.cdf.value(), Source: ev.Flow.Source, 
			Dest: ev.Flow.Dest, LastTime: 0, FinishEvent: nil, 
			ExpType: exptype, InterRack: rand.Intn(RACKS*RACKS) == LUCKY}
		heap.Push(&creationQueue, makeCreationEvent(f))
	}

	// predict top1000 flow
	sort.SliceStable(sortedFlows, func(i, j int) bool { 
					// reverse
					return sortedFlows[j].Size < sortedFlows[i].Size
					})
	for i := 0; i < int(fg.numFlows); i++ {
		prob := rand.Float64()
		if i < 3000 {
			if prob < 0.98{sortedFlows[i].Cls = 1} else {sortedFlows[i].Cls = 0}
		} else {
			if prob < 0.98{sortedFlows[i].Cls = 0} else {sortedFlows[i].Cls = 1}
		}
	}

	return eventQueue
}
