package main

// run ideal event loop until completion.

import (
	"container/heap"
	"container/list"
	"sort"
	"math/rand"
	"fmt"
)


const (
	NUM_HOSTS         = 144
	HOSTS_IN_RACK     = 16
	PROPAGATION_DELAY_IN_RACK = 0.44 // microseconds，光纤传播延迟
	PROPAGATION_DELAY_OUT_RACK = 2.04
	RACKS = int(NUM_HOSTS / HOSTS_IN_RACK) // 9
	LUCKY = 6 // luck number
)

func removeFromActiveFlows(ls *list.List, f *Flow) {
	for e := ls.Front(); e != nil; e = e.Next() {
		if e.Value.(*Flow) == f {
			ls.Remove(e)
			break
		}
	}
}

func getOracleFCT(flow *Flow, bw float64) (float64, float64) {
	var pd float64

	if flow.InterRack {
		pd = PROPAGATION_DELAY_IN_RACK*2 + PROPAGATION_DELAY_OUT_RACK*2
	} else {pd = PROPAGATION_DELAY_IN_RACK*2}
	
	td := (float64(flow.Size) / (bw * 1e9 / 8)) * 1e6 // microseconds
	return pd, td
}

// input: linked list of flows
// output: sorted slice of flows, number of flows
// type SortedFlows []*Flow in flow.go
func getSortedFlows(actives *list.List) SortedFlows {
	sortedFlows := make(SortedFlows, actives.Len())

	i := 0
	for e := actives.Front(); e != nil; e = e.Next() {
		sortedFlows[i] = e.Value.(*Flow)
		i++
	}

	// 在排序切片时会保留相等元素的原始顺序
	sort.SliceStable(sortedFlows, func(i, j int) bool { 
				switch sortedFlows[i].ExpType {
				case SRPT:
					return sortedFlows[i].TimeRemaining < sortedFlows[j].TimeRemaining
				case FIFO:
					return sortedFlows[i].Start < sortedFlows[j].Start
				case RAND:
					if rand.Float64() > 0.5 {
						return true
					} else { return false }
				case PRIOR:
					if sortedFlows[i].Cls == sortedFlows[j].Cls {
						if rand.Float64() > 0.5 {
							return true
						} else { return false }
					}
					return sortedFlows[i].Cls < sortedFlows[j].Cls
			    default:
			    	panic("ExpType(ScheduleType) is not known")
				}})
	// sort.Sort(sortedFlows)
	return sortedFlows
}

// input: eventQueue of FlowArrival events, topology bandwidth (to determine oracle FCT)
// output: slice of pointers to completed Flows
func ideal(num int, bandwidth float64, eventQueue EventQueue) []*Flow {
	heap.Init(&eventQueue)

	activeFlows := list.New()
	completedFlows := make([]*Flow, 0)
	var srcPorts [NUM_HOSTS]*Flow
	var dstPorts [NUM_HOSTS]*Flow
	var currentTime float64

	for len(eventQueue) > 0 {
		// fmt.Printf("len eventQueue: %d\n", len(eventQueue))
		ev := heap.Pop(&eventQueue).(*Event)
		if ev.Cancelled {
			continue
		}

		if ev.Time < currentTime {
			panic("going backwards!")
		}

		currentTime = ev.Time
		flow := ev.Flow

		var propagation float64
		if flow.InterRack {
			propagation = PROPAGATION_DELAY_IN_RACK + PROPAGATION_DELAY_OUT_RACK
		} else { propagation = PROPAGATION_DELAY_IN_RACK }

		switch ev.Type {
		case FlowArrival:
			// logger <- LogEvent{Time: currentTime, Type: LOG_FLOW_ARRIVAL, Flow: flow}
			prop_delay, trans_delay := getOracleFCT(flow, bandwidth)
			flow.TimeRemaining = trans_delay
			flow.OracleFct = prop_delay + trans_delay
			activeFlows.PushBack(flow)
		case FlowSourceFree:
			flow.FinishSending = true
			flow.FinishEvent = makeCompletionEvent(currentTime+propagation, flow, FlowDestFree)
			heap.Push(&eventQueue, flow.FinishEvent)
		case FlowDestFree:
			if !flow.FinishSending {
				panic("finish without finishSending")
			}
			removeFromActiveFlows(activeFlows, flow)
			flow.End = currentTime + propagation
			flow.Finish = true
			completedFlows = append(completedFlows, flow)
			if len(completedFlows)%1000 == 0 {
				mutex.Lock()
				fmt.Printf("Minute: %d, len finish flows: %d\n", num, len(completedFlows))
				mutex.Unlock() 
			}
		}

		for i := 0; i < len(srcPorts); i++ {
			if srcPorts[i] != nil {
				inProgressFlow := srcPorts[i]

				if inProgressFlow.LastTime == 0 {
					panic("flow in progress without LastTime set")
				}

				if inProgressFlow.FinishEvent == nil {
					panic("flow in progress without FinishEvent set")
				}

				inProgressFlow.TimeRemaining -= (currentTime - inProgressFlow.LastTime)
				inProgressFlow.LastTime = 0

				if !inProgressFlow.FinishSending {
					inProgressFlow.FinishEvent.Cancelled = true
					inProgressFlow.FinishEvent = nil
				}
			}
			srcPorts[i] = nil
			dstPorts[i] = nil
		}

		// 只要修改这里 大流排前面就可以了
		sortedActiveFlows := getSortedFlows(activeFlows)
		// fmt.Printf("len sortedActiveFlows: %d\n", len(sortedActiveFlows))

		for _, f := range sortedActiveFlows {
			src := f.Source
			dst := f.Dest

			if f.FinishSending {
				if f.Finish {
					panic("finished flow in actives")
				}

				if srcPorts[src] != nil || dstPorts[dst] != nil {
					panic("ports taken on still sending flow")
				}

				dstPorts[dst] = f
			}
		}


		for _, f := range sortedActiveFlows {
			src := f.Source
			dst := f.Dest

			if srcPorts[src] == nil && dstPorts[dst] == nil {
				//this flow gets scheduled.
				f.LastTime = currentTime
				srcPorts[src] = f
				dstPorts[dst] = f
				// fmt.Printf("this flow gets scheduled: %d %d %d %f\n", f.Size, f.Source, f.Dest, f.Start)

				if f.FinishEvent != nil {
					panic("flow being scheduled, finish event non-nil")
				}

				f.FinishEvent = makeCompletionEvent(currentTime+f.TimeRemaining, f, FlowSourceFree)
				if f.FinishEvent.Time < 0 {
					panic("makeCompletionEvent flow.FinishEvent < 0")
				}
				if f.FinishEvent.Time < 1e6 {
					panic("makeCompletionEvent flow.FinishEvent < 1e6")
				}
				heap.Push(&eventQueue, f.FinishEvent)
			}
		}
	}

	return completedFlows
}
