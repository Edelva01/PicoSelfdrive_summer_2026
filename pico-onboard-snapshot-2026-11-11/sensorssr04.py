from machine import Pin
import time
import config

echo = Pin(config.ECHO_PIN, Pin.IN)
trig = Pin(config.TRIG_PIN, Pin.OUT)

def get_distance_cm():
    # Make sure trigger starts LOW
    trig.value(0)
    time.sleep_us(2)

    # Send 10 microsecond trigger pulse
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    # Wait for echo to go HIGH
    timeout = time.ticks_us()

    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout) > 30000:
            return -1

    start = time.ticks_us()

    # Wait for echo to go LOW
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > 30000:
            return -1

    end = time.ticks_us()

    # Convert time to distance
    duration = time.ticks_diff(end, start)
    distance = (duration * 0.0343) / 2

    return round(distance, 2)