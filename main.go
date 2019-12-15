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
	MAX_PULSE = 1000
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

		var deviceLog = logging.MustGetLogger("PCA9685")

		pca9685 := device.NewPCA9685(i2cDevice, "PWM Controller", MIN_PULSE, MAX_PULSE, deviceLog)

		pca9685.Init()

		pca9685.Demo([]int{0})

		pwm00 := pca9685.NewPwm(0)

		_ = pwm00.SetPercentage(15.0)

		time.Sleep(2 * time.Second)

		pca9685.SwitchOff([]int{0})
	}
}
