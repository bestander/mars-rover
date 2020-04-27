package main

import (
	"os"
	"time"

	"github.com/op/go-logging"
	"github.com/stianeikeland/go-rpio"
)

func init() {
	stderrorLog := logging.NewLogBackend(os.Stderr, "", 0)
	stderrorLogLeveled := logging.AddModuleLevel(stderrorLog)
	stderrorLogLeveled.SetLevel(logging.INFO, "")
	logging.SetBackend(stderrorLogLeveled)
}

func main() {

	var mainLog = logging.MustGetLogger("Rover engines")
	mainLog.Info("Starting")

	err := rpio.Open()
	if err != nil {
		mainLog.Error(err)
		os.Exit(1)
	}
	defer rpio.Close()

	leftSide := rpio.Pin(12)
	rightSide := rpio.Pin(19)
	leftSide.Mode(rpio.Pwm)
	rightSide.Mode(rpio.Pwm)
	leftSide.Freq(5000)
	rightSide.Freq(5000)
	for i := uint32(5); i <= 10; i++ {
		// 5 - fast forward
		// 10 - fast backward
		leftSide.DutyCycle(i, 20)
		rightSide.DutyCycle(i, 20)
		time.Sleep(time.Second * 5)
	}
	leftSide.DutyCycle(0, 20)
	rightSide.DutyCycle(0, 20)
}
