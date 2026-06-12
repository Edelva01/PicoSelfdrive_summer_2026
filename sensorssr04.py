from machine import Pin
import time

echo = Pin(14, Pin.IN)
trig = Pin(15, Pin.OUT)

_last_good_distance = None


def _raw_distance_cm(timeout_us=30000):
    trig.value(0)
    time.sleep_us(2)

    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    timeout = time.ticks_us()

    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), timeout) > timeout_us:
            return -1
    start = time.ticks_us()

    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > timeout_us:
            return -1
    end = time.ticks_us()

    duration = time.ticks_diff(end, start)
    distance = (duration * 0.0343) / 2
    return round(distance, 2)


def _median(values):
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2

def get_distance_cm():
    global _last_good_distance

    samples = []
    for _ in range(7):
        d = _raw_distance_cm()
        # Ignore timeout and out-of-range noise.
        if d != -1 and 2 <= d <= 400:
            samples.append(d)
        time.sleep_ms(15)

    if not samples:
        # Return last known good value if available; otherwise timeout.
        return _last_good_distance if _last_good_distance is not None else -1

    filtered = round(_median(samples), 2)

    # Reject sudden jumps likely caused by stray reflections.
    if _last_good_distance is not None and abs(filtered - _last_good_distance) > 40:
        return _last_good_distance

    _last_good_distance = filtered
    return filtered
