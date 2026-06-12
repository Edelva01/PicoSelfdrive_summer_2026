from machine import Pin
import time


def one_ping(trig_pin_num, echo_pin_num, timeout_us=30000):
    trig = Pin(trig_pin_num, Pin.OUT)
    echo = Pin(echo_pin_num, Pin.IN)

    trig.value(0)
    time.sleep_us(5)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    t0 = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), t0) > timeout_us:
            return ("wait_rise_timeout", None, echo.value())

    t1 = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), t1) > timeout_us:
            return ("wait_fall_timeout", None, echo.value())

    t2 = time.ticks_us()
    dur = time.ticks_diff(t2, t1)
    dist_cm = (dur * 0.0343) / 2
    return ("ok", round(dist_cm, 2), echo.value())


def run_combo(trig_pin_num, echo_pin_num, samples=5):
    print("combo trig=GP{} echo=GP{}".format(trig_pin_num, echo_pin_num))
    vals = []
    for _ in range(samples):
        status, dist, echo_state = one_ping(trig_pin_num, echo_pin_num)
        vals.append((status, dist, echo_state))
        time.sleep_ms(80)
    for i, item in enumerate(vals, 1):
        print("  sample {} -> {}".format(i, item))


print("SR04 diagnostics start")
run_combo(15, 14)
run_combo(14, 15)
print("SR04 diagnostics done")
