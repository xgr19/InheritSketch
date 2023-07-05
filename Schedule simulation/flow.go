package main

// define data types

type SortedFlows []*Flow

type Flow struct {
	Start         float64
	Size          uint
	Source        uint8
	Dest          uint8
	End           float64
	TimeRemaining float64
	OracleFct     float64
	LastTime      float64
	FinishEvent   *Event
	FinishSending bool
	Finish        bool
	ExpType       ScheduleType
	InterRack     bool
	Cls           uint
}

func calculateFlowSlowdown(f *Flow) float64 {
	if f.End < f.Start {
		panic("flow has negative fct")
	}

	fct := (f.End - f.Start)
	slowdown := fct / f.OracleFct
	switch {
	case slowdown >= 1:
		return slowdown
	case slowdown < 0.999:
		panic("flow has fct better than oracle")
	default:
		return 1.000000
	}
}

type EventType int

/*
iota在const关键字出现时将被重置为0(const内部的第一行之前)，
const中每新增一行常量声明将使iota计数一次(iota可理解为const语句块中的行索引)。
使用iota能简化定义，在定义枚举时很有用。
*/
const (
	FlowArrival EventType = iota // 0
	FlowSourceFree				 // 1
	FlowDestFree				 // 2
)

type Event struct {
	Time      float64
	Flow      *Flow
	Type      EventType
	Cancelled bool
}

func makeArrivalEvent(f *Flow) *Event {
	return &Event{Time: f.Start, Flow: f, Type: FlowArrival, Cancelled: false}
}

func makeCompletionEvent(t float64, f *Flow, ty EventType) *Event {
	return &Event{Time: t, Flow: f, Type: ty, Cancelled: false}
}

// EventQueue是类型别名
type EventQueue []*Event

// 为EventQueue添加方法，这些方法供heap调用
func (e EventQueue) Len() int {
	return len(e)
}

func (e EventQueue) Less(i, j int) bool {
	return (e[i].Time < e[j].Time)
}

func (e EventQueue) Swap(i, j int) {
	tmp := e[i]
	e[i] = e[j]
	e[j] = tmp
}

func (e *EventQueue) Push(x interface{}) {
	ev := x.(*Event)
	*e = append(*e, ev)
}

func (e *EventQueue) Pop() interface{} {
	old := *e
	n := len(old)
	ev := old[n-1]
	*e = old[0 : n-1]
	return ev
}
