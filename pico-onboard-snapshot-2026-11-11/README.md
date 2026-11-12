# Pico onboard snapshot — 2026-11-11

These seven MicroPython files are an exact copy of what was on the Pico on 2026-11-11 (Eastern Time). The bytes are unchanged from the board, including CRLF line endings where the onboard files used them.

The Pico is a Raspberry Pi Pico W (USB VID `2E8A:0005`, serial `449113B25ED0E81E`) that appeared as COM3.

| File | Size (bytes) |
| --- | ---: |
| `config.py` | 253 |
| `lcd1602.py` | 3060 |
| `lcdLukas.py` | 1256 |
| `main.py` | 124 |
| `motor.py` | 496 |
| `sensorssr04.py` | 876 |
| `wifi_car.py` | 3004 |

## Comparison to this repo's root at the time of the snapshot

- `main.py` already matched the repo root (same git blob content).
- `motor.py` has the same source text as the repo root. The Pico copy uses CRLF line endings (496 bytes) and the repo-root file uses LF (470 bytes), so the git blobs differ by those carriage returns. Converting CRLF to LF makes the two files identical.
- `wifi_car.py`, `sensorssr04.py`, and `config.py` on the Pico differed from the repo root. The Pico copies are smaller and older (`wifi_car.py` is 3004 bytes on the Pico and 29373 bytes at the repo root). This snapshot keeps the onboard versions. The more complete files at the repo root are left untouched.
- `lcd1602.py` and `lcdLukas.py` were not in this repo. `lcd1602.py` matches the file of the same name in [Edelva01/RC-Police_Car](https://github.com/Edelva01/RC-Police_Car) (same git blob, `87b306744dd24fdee584addb253c1f0702ba28cc`). `lcdLukas.py` was not in any of the user's GitHub repos.

`config.py` contains the WiFi access-point name and password used by the Pico. The repo root already has the same access-point credentials in this public repository. The exact onboard file is included because the Pico's files were requested on GitHub. Those credentials are not copied into any other file.
