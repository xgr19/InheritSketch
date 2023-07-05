package main

// read in input
// initialize objects

/*
局部变量分配在栈，则函数调用结束后销毁。
在C/C++语言中，操作函数返回后的局部变量的地址，一定会发生空指针异常。
要解决这种问题，只需将内存空间分配在堆中即可（new）。但在Go语言中，
函数内部局部变量，无论是动态new出来的变量还是创建的局部变量，
它被分配在堆还是栈，是由编译器做“逃逸分析”之后做出的决定：
果编译器无法证明函数返回后是否还有该变量的引用存在，则编译器为避免悬挂空指针的错误，
就会将该局部变量分配在堆空间中。
*/ 

import (
	"fmt"
	"os"
	"sync"
	"time"
)

var mutex sync.Mutex
const MINUTES = 30

type ScheduleType int
const (
	SRPT ScheduleType = iota // 0
	FIFO				     // 1
	RAND					 // 2
	PRIOR
)
// 定义 ScheduleType 类型的方法 String(), 返回字符串。
func (t ScheduleType) String() string {
	switch t {
	case SRPT: return "SRPT"
	case FIFO: return "FIFO"
	case RAND: return "RAND"
	case PRIOR: return "PRIOR"
	default:
		panic("Invalid ScheduleType")
	}
}

type Conf struct {
	Bandwidth     float64
	Load          float64
	NumFlows      uint
	CDFFileName   string
	ExpType 	  ScheduleType
}

type FlowComTime struct {
	Tot    float64
	Idl    float64
}

func check(e error) {
	if e != nil {
		panic(e)
	}
}

func WriteString(file *os.File, str string) {
	_, err := file.WriteString(str)
	check(err)
}

//@brief：耗时统计函数
func timeCost() func() {
	start := time.Now()
	return func() {
		tc:=time.Since(start)
		fmt.Printf("simulation time = %v\n\n", tc)
	}
}


func run_exp(num int, fct chan FlowComTime, cdfname string, conf Conf) {
	// type EventQueue []*Event defined in flow.go
	var eventQueue EventQueue
	fg := makeFlowGenerator(conf.Load, conf.Bandwidth, cdfname, conf.NumFlows)
	eventQueue = fg.makeFlows(conf.ExpType)

	finishflows := ideal(num, conf.Bandwidth, eventQueue)
	numFlows := len(finishflows)

	slowdown := 0.0
	avg_fct, avg_ideal_fct := 0.0, 0.0
	for i := 0; i < numFlows; i++ {
		slowdown += calculateFlowSlowdown(finishflows[i])
		avg_fct += (finishflows[i].End - finishflows[i].Start)
		avg_ideal_fct += finishflows[i].OracleFct
	}

	mutex.Lock()
	fmt.Printf("************************ Process minute: %d finishes\n", num)
	// fmt.Printf("FCT(ms): %f, Ideal FCT(ms): %f, Slow down: %f\n", 
	// 	avg_fct/float64(numFlows)/1e3, avg_ideal_fct/float64(numFlows)/1e3, slowdown/float64(numFlows))
	mutex.Unlock() 
	fct <- FlowComTime{Tot:avg_fct/float64(numFlows)/1e3, Idl:avg_ideal_fct/float64(numFlows)/1e3}
}


func main() {
	args := os.Args[1:]
	var expt ScheduleType
	switch args[0]{
	case "SRPT": expt = SRPT
	case "FIFO": expt = FIFO
	case "RAND": expt = RAND
	case "PRIOR": expt = PRIOR
	default:
		panic(fmt.Sprintf("Invalid ScheduleType: %s", args[0]))
	}
	
	defer timeCost()()	//注意，是对 timeCost()返回的函数进行调用，因此需要加两对小括号
	linkloads := [...]float64{0.5, 0.6, 0.8, 0.9}
	dir := "/data/xgr/XIE416Sketch/cdfs/"
	datasets := [...]string{"CAIDA18", "CAIDA19", "CERNET"}
	paths := [...]string{
			dir+"equinix-nyc.dirA.20180315-13%02d00.UTC.anon.npy.cdf.txt",
			dir+"equinix-nyc.dirA.20190117-13%02d00.UTC.anon.npy.cdf.txt",
			dir+"20201227_14%02d00_ingress.npy.cdf.txt",
		}

	file, err := os.Create(fmt.Sprintf("%s.txt", expt.String()))
	check(err)
	defer file.Close()
	WriteString(file, fmt.Sprintf("Start time = %v\n\n", time.Now()))

	for _, load := range linkloads {
		for j, _ := range datasets {
			conf := Conf{Bandwidth: 10, Load: load, NumFlows: 100000, 
				ExpType: expt, CDFFileName: paths[j]}
			
			WriteString(file, fmt.Sprintf("======== This is: %s %s ========\n", conf.ExpType.String(), datasets[j]))
			WriteString(file, fmt.Sprintf("Load: %.2f, Flows: %d, Band: %.2fGbps\n", conf.Load, conf.NumFlows, conf.Bandwidth))

			fcts := make([]chan FlowComTime, MINUTES)
			for i := 0; i < MINUTES; i++ {
				fcts[i] = make(chan FlowComTime)
				go run_exp(i, fcts[i], fmt.Sprintf(conf.CDFFileName, i), conf)
			}

			tot, idl := 0.0, 0.0
			for _, fct := range fcts {
				tmp := <- fct
				tot += tmp.Tot
				idl += tmp.Idl
			}
			WriteString(file, fmt.Sprintf("Tot FCT: %.4fms, Ideal FCT: %.4fms\n", tot, idl))
		}

		WriteString(file, fmt.Sprintf("%s", "\n"))
	}
}
