import network
import socket
import time
import motor
import sensorssr04

AP_NAME = "Pico-Smart-Car"
AP_PASSWORD = "12345678"
TOO_CLOSE_CM = 15
AUTO_DECISION_INTERVAL_MS = 250

car_started = False
drive_mode = "manual"
last_action = "stopped"
last_distance = -1

def webpage(distance):
    status_text = "RUNNING" if car_started else "STOPPED"
    mode_text = "AUTO" if drive_mode == "auto" else "MANUAL"
    self_drive_text = "ON" if (car_started and drive_mode == "auto") else "OFF"
    auto_btn_class = "active" if drive_mode == "auto" else ""
    manual_btn_class = "active" if drive_mode == "manual" else ""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Pico Smart Car</title>
    <meta http-equiv="refresh" content="1">
    <style>
        body { font-family: Arial; text-align: center; }
        button { font-size: 28px; padding: 18px; margin: 8px; width: 180px; }
        .distance { font-size: 40px; font-weight: bold; color: blue; }
        .status { font-size: 22px; margin: 8px 0; }
        .small { font-size: 18px; }
        .banner { font-size: 28px; font-weight: bold; margin: 12px auto; padding: 10px; width: 340px; border-radius: 8px; }
        .on { background: #d8ffd8; color: #0a6f0a; border: 2px solid #0a6f0a; }
        .off { background: #ffe5e5; color: #8a1010; border: 2px solid #8a1010; }
        .active { border: 4px solid #111; }
    </style>
</head>
<body>
    <h1>Pico Smart Car</h1>

    <div class="banner """ + ("on" if self_drive_text == "ON" else "off") + """>SELF DRIVING: """ + self_drive_text + """</div>

    <div class="status"><b>Status:</b> """ + status_text + """</div>
    <div class="status"><b>Mode:</b> """ + mode_text + """</div>
    <div class="status small"><b>Last Action:</b> """ + last_action + """</div>

    <h2>Ultrasonic Distance</h2>
    <div class="distance">""" + str(distance) + """ cm</div>
    <div class="small">Auto reverse threshold: """ + str(TOO_CLOSE_CM) + """ cm</div>

    <br>

    <a href="/start"><button>Start</button></a>
    <a href="/stopcar"><button>Stop Car</button></a><br>
    <a href="/manual"><button class='""" + manual_btn_class + """'>Manual</button></a>
    <a href="/auto"><button class='""" + auto_btn_class + """'>Self Drive</button></a><br>

    <a href="/forward"><button>Forward</button></a><br>
    <a href="/left"><button>Left</button></a>
    <a href="/stop"><button>Stop</button></a>
    <a href="/right"><button>Right</button></a><br>
    <a href="/backward"><button>Backward</button></a>

</body>
</html>
"""

def start():
    global car_started, drive_mode, last_action, last_distance

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_NAME, password=AP_PASSWORD)

    while not ap.active():
        time.sleep(1)

    print("Access Point Active")
    print(ap.ifconfig())
    print("Connect to WiFi:", AP_NAME)
    print("Go to: http://192.168.4.1")

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    s = socket.socket()
    s.bind(addr)
    s.listen(1)
    # Keep the server loop responsive so auto-drive can run even with no clients connected.
    s.settimeout(0.2)

    last_auto_tick = time.ticks_ms()

    while True:
        request = ""
        conn = None

        try:
            conn, addr = s.accept()
            request = conn.recv(1024).decode()
            print(request)
        except OSError:
            # Timeout/no client this tick.
            pass

        if "/start" in request:
            car_started = True
            last_action = "start"
        elif "/stopcar" in request:
            car_started = False
            motor.stop()
            last_action = "stop"
        elif "/manual" in request:
            drive_mode = "manual"
            last_action = "manual mode"
        elif "/auto" in request:
            drive_mode = "auto"
            last_action = "auto mode"

        if drive_mode == "manual":
            if "/forward" in request:
                motor.forward()
                last_action = "manual forward"
            elif "/backward" in request:
                motor.backward()
                last_action = "manual backward"
            elif "/left" in request:
                motor.left()
                last_action = "manual left"
            elif "/right" in request:
                motor.right()
                last_action = "manual right"
            elif "/stop" in request:
                motor.stop()
                last_action = "manual stop"

        now = time.ticks_ms()
        if time.ticks_diff(now, last_auto_tick) >= AUTO_DECISION_INTERVAL_MS:
            last_auto_tick = now
            last_distance = sensorssr04.get_distance_cm()

            if car_started and drive_mode == "auto":
                if last_distance != -1 and last_distance < TOO_CLOSE_CM:
                    motor.backward()
                    last_action = "auto backward"
                else:
                    motor.forward()
                    last_action = "auto forward"
            elif not car_started:
                motor.stop()

        if conn is not None:
            response = webpage(last_distance)
            conn.send("HTTP/1.1 200 OK\r\n")
            conn.send("Content-Type: text/html\r\n")
            conn.send("Cache-Control: no-store, no-cache, must-revalidate, max-age=0\r\n")
            conn.send("Pragma: no-cache\r\n")
            conn.send("Expires: 0\r\n")
            conn.send("Connection: close\r\n\r\n")
            conn.sendall(response)
            conn.close()