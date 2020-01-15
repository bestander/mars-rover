package main

import (
	"os"
	"time"

	"github.com/op/go-logging"
	"github.com/sergiorb/pca9685-golang/device"
	"golang.org/x/exp/io/i2c"
)

const (
	I2C_ADDR  = "/dev/i2c-1"
	ADDR_01   = 0x40
	MIN_PULSE = 0
	MAX_PULSE = 5000
)

func init() {

	stderrorLog := logging.NewLogBackend(os.Stderr, "", 0)

	stderrorLogLeveled := logging.AddModuleLevel(stderrorLog)
	stderrorLogLeveled.SetLevel(logging.INFO, "")

	logging.SetBackend(stderrorLogLeveled)
}

func main() {

	var mainLog = logging.MustGetLogger("PCA9685 Demo")

	i2cDevice, err := i2c.Open(&i2c.Devfs{Dev: I2C_ADDR}, ADDR_01)
	defer i2cDevice.Close()

	if err != nil {

		mainLog.Error(err)

	} else {

		// self.PWMA = 0
		// self.AIN1 = 1
		// self.AIN2 = 2
		// self.PWMB = 5
		// self.BIN1 = 3
		// self.BIN2 = 4

		var deviceLog = logging.MustGetLogger("PCA9685")

		pca9685 := device.NewPCA9685(i2cDevice, "PWM Controller", MIN_PULSE, MAX_PULSE, deviceLog)
		// pca9685.Frequency = 50
		pca9685.Init()

		pwm := pca9685.NewPwm(0)
		pwm.SetPulse(0, 4096)
		pwm.SetPercentage(100.0)

		// set level
		ain1 := pca9685.NewPwm(1)
		ain1.SetPulse(0, 0)
		ain2 := pca9685.NewPwm(2)
		ain2.SetPulse(0, 4095)

		time.Sleep(3 * time.Second)

		pca9685.SwitchOff([]int{1, 2, 3})
	}
}
