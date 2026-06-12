import network
import socket
import time
from machine import Pin
import motor
import sensorssr04
import config

AP_NAME = "Pico-Smart-Car"
AP_PASSWORD = "12345678"
BRAND_H1 = "Turtleback Robotics Academy"
BRAND_H2 = "Summer Camp 2026"
TOO_CLOSE_CM = 15
AUTO_DECISION_INTERVAL_MS = 250
SERVER_TIMEOUT_SEC = 0.2
ACTION_DEBOUNCE_MS = 250
REQUEST_LOG_ENABLED = False

STATE = {
    "car_started": False,
    "drive_mode": "manual",
    "last_action": "stopped",
    "last_distance": -1,
    "headlight_enabled": False,
    "current_motion": "stopped",
    "brake_until_ms": 0,
}

LAST_ACTION_TS = {}

RED_LIGHT = Pin(config.RED_LIGHT_PIN, Pin.OUT)
WHITE_LIGHT = Pin(config.WHITE_LIGHT_PIN, Pin.OUT)
RED_LIGHT.value(0)
WHITE_LIGHT.value(0)


def log_error(context, err):
    print("ERROR:", context, err)


def apply_lights():
    try:
        now = time.ticks_ms()
        brake_active = time.ticks_diff(STATE["brake_until_ms"], now) > 0
        RED_LIGHT.value(1 if brake_active else 0)
        WHITE_LIGHT.value(1 if STATE["headlight_enabled"] else 0)
    except Exception as err:
        log_error("apply_lights", err)


def trigger_brake_light(duration_ms=1000):
    STATE["brake_until_ms"] = time.ticks_add(time.ticks_ms(), duration_ms)
    apply_lights()


def set_motion(motion):
    STATE["current_motion"] = motion
    try:
        if motion == "forward":
            motor.forward()
        elif motion == "backward":
            motor.backward()
        elif motion == "left":
            motor.left()
        elif motion == "right":
            motor.right()
        else:
            motor.stop()
    except Exception as err:
        log_error("set_motion", err)
        try:
            motor.stop()
        except Exception as stop_err:
            log_error("set_motion_stop_fallback", stop_err)
    apply_lights()


def should_process_action(action_key):
    # Debounce non-drive actions so duplicate taps/requests don't flap state.
    now = time.ticks_ms()
    last_ts = LAST_ACTION_TS.get(action_key)
    if last_ts is not None and time.ticks_diff(now, last_ts) < ACTION_DEBOUNCE_MS:
        return False
    LAST_ACTION_TS[action_key] = now
    return True


def parse_request_path(raw_request):
    try:
        first_line = raw_request.split("\r\n", 1)[0]
        parts = first_line.split(" ")
        if len(parts) >= 2:
            return parts[1]
    except Exception as err:
        log_error("parse_request_path", err)
    return "/"


def log_request_line(raw_request):
    if not REQUEST_LOG_ENABLED:
        return
    try:
        first_line = raw_request.split("\r\n", 1)[0]
        print(first_line)
    except Exception as err:
        log_error("log_request_line", err)


def parse_route_and_params(path):
    if "?" not in path:
        return path, {}

    route, query = path.split("?", 1)
    params = {}
    for pair in query.split("&"):
        if not pair:
            continue
        if "=" in pair:
            k, v = pair.split("=", 1)
            params[k] = v
        else:
            params[pair] = ""
    return route, params


def build_page(distance):
    status_text = "RUNNING" if STATE["car_started"] else "STOPPED"
    mode_text = "AUTO" if STATE["drive_mode"] == "auto" else "MANUAL"
    self_drive_text = "ON" if (STATE["car_started"] and STATE["drive_mode"] == "auto") else "OFF"
    headlight_text = "ON" if STATE["headlight_enabled"] else "OFF"
    return """<!DOCTYPE html>
<html>
<head>
    <title>Pico Smart Car</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; text-align: center; }
        button { font-size: 22px; padding: 14px; margin: 6px; min-width: 140px; }
        .brand-h1 { margin: 10px 0 2px 0; }
        .brand-h2 { margin: 0 0 10px 0; font-weight: 600; color: #333; }
        .distance { font-size: 40px; font-weight: bold; color: blue; }
        .status { font-size: 22px; margin: 8px 0; }
        .small { font-size: 18px; }
        .banner { font-size: 28px; font-weight: bold; margin: 12px auto; padding: 10px; width: 340px; border-radius: 8px; }
        .on { background: #d8ffd8; color: #0a6f0a; border: 2px solid #0a6f0a; }
        .off { background: #ffe5e5; color: #8a1010; border: 2px solid #8a1010; }
        .toggle-on { background: #d8ffd8; border: 2px solid #0a6f0a; color: #0a6f0a; }
        .toggle-off { background: #ffe5e5; border: 2px solid #8a1010; color: #8a1010; }
        .toggle-neutral { background: #fff6d8; border: 2px solid #8a6f10; color: #6a5208; }
        .row { margin: 8px 0; }
        .pad { width: 260px; margin: 10px auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
        .pad button { min-width: 0; width: 100%; height: 72px; border-radius: 16px; font-size: 26px; }
        .ghost { visibility: hidden; }
    </style>
</head>
<body>
    <h1 class="brand-h1">""" + BRAND_H1 + """</h1>
    <h2 class="brand-h2">""" + BRAND_H2 + """</h2>

    <div class="banner """ + ("on" if self_drive_text == "ON" else "off") + """>SELF DRIVING: """ + self_drive_text + """</div>

    <div id="status-line" class="status"><b>Status:</b> """ + status_text + """</div>

    <h2>Ultrasonic Distance</h2>
    <div class="distance">""" + str(distance) + """ cm</div>
    <div class="small">Auto reverse threshold: """ + str(TOO_CLOSE_CM) + """ cm</div>

    <div class="row">
        <button id="btn-power" onclick="togglePower()">Start Car</button>
    </div>
    <div class="row">
        <button id="btn-mode" onclick="toggleMode()">Switch To Auto</button>
    </div>
    <div class="row">
        <button id="btn-headlight" onclick="toggleHeadlight()">Headlight: OFF</button>
    </div>

    <h2>Drive Pad (Hold)</h2>
    <div class="pad">
        <button class="ghost"></button>
        <button id="btn-up">▲</button>
        <button class="ghost"></button>
        <button id="btn-left">◀</button>
        <button id="btn-stop">■</button>
        <button id="btn-right">▶</button>
        <button class="ghost"></button>
        <button id="btn-down">▼</button>
        <button class="ghost"></button>
    </div>

    <script>
        var LAST_STATUS = null;

        function applyStatus(s) {
            LAST_STATUS = s;
            var b = document.querySelector('.banner');
            if (b) {
                b.textContent = 'SELF DRIVING: ' + s.self_drive;
                b.className = 'banner ' + (s.self_drive === 'ON' ? 'on' : 'off');
            }
            var statusLine = document.getElementById('status-line');
            if (statusLine) statusLine.innerHTML = '<b>Status:</b> ' + s.status;
            var d = document.querySelector('.distance');
            if (d) d.textContent = s.distance + ' cm';

            var power = document.getElementById('btn-power');
            if (power) {
                if (s.status === 'RUNNING') {
                    power.textContent = 'Stop Car';
                    power.className = 'toggle-off';
                } else {
                    power.textContent = 'Start Car';
                    power.className = 'toggle-on';
                }
            }

            var mode = document.getElementById('btn-mode');
            if (mode) {
                if (s.mode === 'AUTO') {
                    mode.textContent = 'Switch To Manual';
                    mode.className = 'toggle-neutral';
                } else {
                    mode.textContent = 'Switch To Auto';
                    mode.className = 'toggle-neutral';
                }
            }

            var headlight = document.getElementById('btn-headlight');
            if (headlight) {
                if (s.headlight === 'ON') {
                    headlight.textContent = 'Headlight: ON (Tap For OFF)';
                    headlight.className = 'toggle-on';
                } else {
                    headlight.textContent = 'Headlight: OFF (Tap For ON)';
                    headlight.className = 'toggle-off';
                }
            }
        }

        function cmd(name) {
            return fetch('/api/cmd?name=' + name, { cache: 'no-store' })
                .then(function(r){ return r.json(); })
                .then(function(res){
                    if (res && res.status) {
                        applyStatus(res);
                    }
                    return res;
                })
                .catch(function(){
                    return updateStatus();
                });
        }

        function togglePower() {
            if (LAST_STATUS && LAST_STATUS.status === 'RUNNING') {
                return cmd('stopcar');
            }
            return cmd('start');
        }

        function toggleMode() {
            if (LAST_STATUS && LAST_STATUS.mode === 'AUTO') {
                return cmd('manual');
            }
            return cmd('auto');
        }

        function toggleHeadlight() {
            if (LAST_STATUS && LAST_STATUS.headlight === 'ON') {
                return cmd('headlight_off');
            }
            return cmd('headlight_on');
        }

        function bindHold(buttonId, moveName) {
            var el = document.getElementById(buttonId);
            if (!el) return;

            function down(ev) {
                ev.preventDefault();
                cmd('manual').then(function(){ cmd(moveName); });
            }

            function up(ev) {
                ev.preventDefault();
                cmd('stop');
            }

            el.addEventListener('pointerdown', down);
            el.addEventListener('pointerup', up);
            el.addEventListener('pointercancel', up);
            el.addEventListener('pointerleave', up);
        }

        bindHold('btn-up', 'forward');
        bindHold('btn-down', 'backward');
        bindHold('btn-left', 'left');
        bindHold('btn-right', 'right');

        var stopBtn = document.getElementById('btn-stop');
        if (stopBtn) {
            stopBtn.addEventListener('pointerdown', function(ev){ ev.preventDefault(); cmd('stop'); });
        }

        function updateStatus() {
            return fetch('/api/status', { cache: 'no-store' })
                .then(function(r){ return r.json(); })
                .then(function(s){
                    applyStatus(s);
                    return s;
                })
                .catch(function(){});
        }

        setInterval(updateStatus, 500);
        updateStatus();
    </script>

</body>
</html>
"""


def send_bytes(conn, payload):
    try:
        conn.sendall(payload)
        return True
    except Exception as err:
        log_error("send_bytes", err)
        return False


def send_redirect(conn):
    payload = (
        b"HTTP/1.1 303 See Other\r\n"
        b"Location: /\r\n"
        b"Cache-Control: no-store, no-cache, must-revalidate, max-age=0\r\n"
        b"Connection: close\r\n\r\n"
    )
    send_bytes(conn, payload)


def send_no_content(conn):
    send_bytes(conn, b"HTTP/1.1 204 No Content\r\nConnection: close\r\n\r\n")


def send_html(conn, html):
    response_bytes = html.encode()
    headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "Cache-Control: no-store, no-cache, must-revalidate, max-age=0\r\n"
        "Pragma: no-cache\r\n"
        "Expires: 0\r\n"
        "Connection: close\r\n\r\n"
    ).format(len(response_bytes)).encode()
    if send_bytes(conn, headers):
        send_bytes(conn, response_bytes)


def build_status_json():
    status_text = "RUNNING" if STATE["car_started"] else "STOPPED"
    mode_text = "AUTO" if STATE["drive_mode"] == "auto" else "MANUAL"
    self_drive_text = "ON" if (STATE["car_started"] and STATE["drive_mode"] == "auto") else "OFF"
    headlight_text = "ON" if STATE["headlight_enabled"] else "OFF"
    last_action_text = STATE["last_action"].replace('"', "'")
    return (
        '{{"status":"{}","mode":"{}","self_drive":"{}","headlight":"{}",'
        '"last_action":"{}","distance":{}}}'
    ).format(
        status_text,
        mode_text,
        self_drive_text,
        headlight_text,
        last_action_text,
        STATE["last_distance"],
    )


def build_cmd_ack_json(command_name, applied):
    status = build_status_json()[:-1]
    safe_command_name = command_name.replace('"', "'")
    return '{"ok":%s,"command":"%s",%s' % (
        "true" if applied else "false",
        safe_command_name,
        status[1:],
    )


def send_json(conn, payload):
    payload_bytes = payload.encode()
    headers = (
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: application/json; charset=utf-8\r\n"
        "Content-Length: {}\r\n"
        "Cache-Control: no-store, no-cache, must-revalidate, max-age=0\r\n"
        "Connection: close\r\n\r\n"
    ).format(len(payload_bytes)).encode()
    if send_bytes(conn, headers):
        send_bytes(conn, payload_bytes)


def safe_close(conn):
    if conn is None:
        return
    try:
        conn.close()
    except Exception as err:
        log_error("safe_close", err)


def receive_request(server_socket):
    try:
        conn, _ = server_socket.accept()
        conn.settimeout(0.25)
        raw = conn.recv(1024).decode("utf-8", "ignore")
        path = parse_request_path(raw)
        log_request_line(raw)
        return conn, path
    except OSError:
        return None, "/"
    except Exception as err:
        log_error("receive_request", err)
        return None, "/"


def apply_command(command_name):
    if command_name == "start":
        if should_process_action("start"):
            STATE["car_started"] = True
            STATE["last_action"] = "start"
            return True
        return False

    if command_name == "stopcar":
        if should_process_action("stopcar"):
            STATE["car_started"] = False
            set_motion("stopped")
            trigger_brake_light()
            STATE["last_action"] = "stop"
            return True
        return False

    if command_name == "manual":
        if should_process_action("manual"):
            STATE["drive_mode"] = "manual"
            STATE["last_action"] = "manual mode"
            return True
        return False

    if command_name == "auto":
        if should_process_action("auto"):
            STATE["drive_mode"] = "auto"
            STATE["last_action"] = "auto mode"
            return True
        return False

    if command_name == "headlight_on":
        if should_process_action("headlight_on"):
            STATE["headlight_enabled"] = True
            apply_lights()
            STATE["last_action"] = "headlight on"
            return True
        return False

    if command_name == "headlight_off":
        if should_process_action("headlight_off"):
            STATE["headlight_enabled"] = False
            apply_lights()
            STATE["last_action"] = "headlight off"
            return True
        return False

    if STATE["drive_mode"] == "manual":
        if command_name == "forward":
            set_motion("forward")
            STATE["last_action"] = "manual forward"
            return True
        if command_name == "backward":
            set_motion("backward")
            STATE["last_action"] = "manual backward"
            return True
        if command_name == "left":
            set_motion("left")
            STATE["last_action"] = "manual left"
            return True
        if command_name == "right":
            set_motion("right")
            STATE["last_action"] = "manual right"
            return True
        if command_name == "stop":
            set_motion("stopped")
            trigger_brake_light()
            STATE["last_action"] = "manual stop"
            return True

    return False


def handle_state_path(path):
    if path == "/start":
        return apply_command("start")

    if path == "/stopcar":
        return apply_command("stopcar")

    if path == "/manual":
        return apply_command("manual")

    if path == "/auto":
        return apply_command("auto")

    if path == "/headlight/on" or path == "/lights/on":
        return apply_command("headlight_on")

    if path == "/headlight/off" or path == "/lights/off":
        return apply_command("headlight_off")

    return False


def handle_manual_path(path):
    if STATE["drive_mode"] != "manual":
        return False

    if path == "/forward":
        return apply_command("forward")
    if path == "/backward":
        return apply_command("backward")
    if path == "/left":
        return apply_command("left")
    if path == "/right":
        return apply_command("right")
    if path == "/stop":
        return apply_command("stop")

    return False


def read_distance_safe():
    try:
        return sensorssr04.get_distance_cm()
    except Exception as err:
        log_error("read_distance_safe", err)
        return -1


def run_auto_tick(last_auto_tick):
    now = time.ticks_ms()
    if time.ticks_diff(now, last_auto_tick) < AUTO_DECISION_INTERVAL_MS:
        return last_auto_tick

    STATE["last_distance"] = read_distance_safe()
    if STATE["car_started"] and STATE["drive_mode"] == "auto":
        if STATE["last_distance"] != -1 and STATE["last_distance"] < TOO_CLOSE_CM:
            set_motion("backward")
            STATE["last_action"] = "auto backward"
        else:
            set_motion("forward")
            STATE["last_action"] = "auto forward"
    elif not STATE["car_started"]:
        set_motion("stopped")

    return now


def respond(conn, path, action_requested, route, params):
    if conn is None:
        return

    try:
        if path == "/favicon.ico":
            send_no_content(conn)
        elif route == "/api/status":
            send_json(conn, build_status_json())
        elif route == "/api/cmd":
            command_name = params.get("name", "")
            applied = apply_command(command_name)
            send_json(conn, build_cmd_ack_json(command_name, applied))
        elif action_requested:
            send_redirect(conn)
        else:
            send_html(conn, build_page(STATE["last_distance"]))
    except Exception as err:
        log_error("respond", err)
        try:
            send_html(conn, "<html><body><h1>Server Error</h1></body></html>")
        except Exception as inner_err:
            log_error("respond_fallback", inner_err)
    finally:
        safe_close(conn)


def setup_access_point():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=AP_NAME, password=AP_PASSWORD)
    while not ap.active():
        time.sleep(1)

    print("Access Point Active")
    print(ap.ifconfig())
    print("Connect to WiFi:", AP_NAME)
    print("Go to: http://192.168.4.1")


def setup_server_socket():
    addr = socket.getaddrinfo("0.0.0.0", 80)[0][-1]
    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(4)
    server_socket.settimeout(SERVER_TIMEOUT_SEC)
    return server_socket


def loop(server_socket):
    last_auto_tick = time.ticks_ms()

    while True:
        conn, path = receive_request(server_socket)
        route, params = parse_route_and_params(path)
        state_action = handle_state_path(route)
        manual_action = handle_manual_path(route)
        action_requested = state_action or manual_action

        last_auto_tick = run_auto_tick(last_auto_tick)
        apply_lights()
        respond(conn, path, action_requested, route, params)


def start():
    try:
        setup_access_point()
        server_socket = setup_server_socket()
        loop(server_socket)
    except Exception as err:
        log_error("start", err)
        raise