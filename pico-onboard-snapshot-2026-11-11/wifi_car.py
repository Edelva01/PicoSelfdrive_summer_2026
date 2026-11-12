import network
import socket
import time
import motor
import sensorssr04
import config


def webpage(distance):
    return """<!DOCTYPE html>
<html>
<head>
    <title>Turtleback Robotics Academy</title>

    <meta http-equiv="refresh" content="1">

    <style>
        body {
            font-family: Arial;
            text-align: center;
            margin: 0;
            background-color: #f4f4f4;
        }

        .header {
            background-color: #004c99;
            color: white;
            padding: 15px;
        }

        .distance {
            font-size: 42px;
            font-weight: bold;
            color: #0066cc;
            margin: 20px;
        }

        button {
            font-size: 28px;
            padding: 18px;
            margin: 8px;
            width: 200px;
            border-radius: 10px;
            border: none;
        }

        .forward {
            background-color: #4CAF50;
            color: white;
        }

        .stop {
            background-color: #d9534f;
            color: white;
        }

        .backward {
            background-color: #f0ad4e;
            color: white;
        }
    </style>

</head>

<body>

<div class="header">
    <h1>Turtleback Robotics Academy</h1>
</div>

<h2>Pico Smart Car Control Center</h2>

<h3>Ultrasonic Distance</h3>

<div class="distance">""" + str(distance) + """ cm</div>

<br>

<a href="/forward">
<button class="forward">Forward</button>
</a>

<br>

<a href="/stop">
<button class="stop">Stop</button>
</a>

<br>

<a href="/backward">
<button class="backward">Backward</button>
</a>

</body>
</html>
"""


def start():

    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    ap.config(
        essid=config.AP_NAME,
        password=config.AP_PASSWORD
    )

    while not ap.active():
        time.sleep(1)

    print()
    print("Access Point Active")
    print(ap.ifconfig())
    print("Connect to WiFi:", config.AP_NAME)
    print("Go to: http://192.168.4.1")
    print()

    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]

    s = socket.socket()

    try:
        s.setsockopt(socket.SOL_SOCKET,
                     socket.SO_REUSEADDR,
                     1)
    except:
        pass

    s.bind(addr)
    s.listen(1)

    while True:

        conn, addr = s.accept()

        request = conn.recv(1024).decode()

        print("Request Received")

        if "/forward" in request:
            motor.forward()

        elif "/backward" in request:
            motor.backward()

        elif "/stop" in request:
            motor.stop()

        distance = sensorssr04.get_distance_cm()

        response = webpage(distance)

        conn.send("HTTP/1.1 200 OK\r\n")
        conn.send("Content-Type: text/html\r\n")
        conn.send("Connection: close\r\n\r\n")
        conn.sendall(response)

        conn.close()