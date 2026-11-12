from machine import Pin
import motor
import wifi_car

led = Pin("LED", Pin.OUT)
led.value(1)

motor.stop()

wifi_car.start()