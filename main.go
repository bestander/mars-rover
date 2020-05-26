package main

import (
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/stianeikeland/go-rpio"
)

func testMotors() {
	err := rpio.Open()
	if err != nil {
		fmt.Println(err)
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

func main() {

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintf(w, "Hello, you've requested: %s\n", r.URL.Path)
		// testMotors()
	})

	http.ListenAndServe(":8080", nil)
}
