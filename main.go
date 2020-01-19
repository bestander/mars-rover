package main

import (
	"os"
	"time"

	"github.com/op/go-logging"
	"github.com/sergiorb/pca9685-golang/device"
	"golang.org/x/exp/io/i2c"
)

type Direction int
type Drive int

const (
	i2cAddr            = "/dev/i2c-1"
	addr01             = 0x40
	minPulse           = 0
	maxPulse           = 5000
	pwmA               = 0
	aIn1               = 1
	aIn2               = 2
	bIn1               = 3
	bIn2               = 4
	pwmB               = 5
	driveA   Drive     = iota
	driveB   Drive     = iota
	forward  Direction = iota
	backward Direction = iota
)

func init() {

	stderrorLog := logging.NewLogBackend(os.Stderr, "", 0)

	stderrorLogLeveled := logging.AddModuleLevel(stderrorLog)
	stderrorLogLeveled.SetLevel(logging.INFO, "")

	logging.SetBackend(stderrorLogLeveled)
}

type PCA9685_DRIVE struct {
	pwmA *device.Pwm
	aIn1 *device.Pwm
	aIn2 *device.Pwm
	pwmB *device.Pwm
	bIn1 *device.Pwm
	bIn2 *device.Pwm
	pca  *device.PCA9685
}

func (p *PCA9685_DRIVE) drive(drive Drive, direction Direction) {
	if drive == driveA {
		if direction == forward {
			p.aIn1.SetPulse(0, 0)
			p.aIn2.SetPulse(0, 4095)

		} else {
			p.aIn2.SetPulse(0, 0)
			p.aIn1.SetPulse(0, 4095)
		}
		p.pwmA.SetPulse(0, 4096)
		p.pwmA.SetPercentage(100.0)
	} else {
		if direction == forward {
			p.bIn1.SetPulse(0, 0)
			p.bIn2.SetPulse(0, 4095)
		} else {
			p.bIn2.SetPulse(0, 0)
			p.bIn1.SetPulse(0, 4095)
		}
		p.pwmB.SetPulse(0, 4096)
		p.pwmB.SetPercentage(100.0)
	}
}

func (p *PCA9685_DRIVE) stop() {
	p.pca.SwitchOff([]int{pwmA, aIn1, aIn2, pwmB, bIn1, bIn2})
}

func main() {

	var mainLog = logging.MustGetLogger("PCA9685 Demo")

	i2cDevice, err := i2c.Open(&i2c.Devfs{Dev: i2cAddr}, addr01)
	defer i2cDevice.Close()

	if err != nil {
		mainLog.Error(err)
	} else {
		var deviceLog = logging.MustGetLogger("PCA9685")
		pca9685 := device.NewPCA9685(i2cDevice, "PWM Controller", minPulse, maxPulse, deviceLog)
		// pca9685.Frequency = 50
		pca9685.Init()

		var drive = PCA9685_DRIVE{
			pwmA: pca9685.NewPwm(pwmA),
			pwmB: pca9685.NewPwm(pwmB),
			aIn1: pca9685.NewPwm(aIn1),
			aIn2: pca9685.NewPwm(aIn2),
			bIn1: pca9685.NewPwm(bIn1),
			bIn2: pca9685.NewPwm(bIn2),
			pca:  pca9685,
		}
		drive.drive(driveA, forward)
		time.Sleep(8 * time.Second)
		drive.drive(driveA, backward)
		time.Sleep(8 * time.Second)
		drive.stop()
		time.Sleep(3 * time.Second)
	}
}
