# Pico Connection Lesson Plan

## Goal
Build a reliable workflow for Raspberry Pi Pico 2 W development in VS Code without random COM port conflicts.

## Core Rule
Only one tool can own COM3 at a time.

- Automation mode: mpremote owns COM3
- Interactive mode: MicroPico vREPL owns COM3

Do not run both modes at the same time.

## Tools We Will Use
- mpremote for repeatable automation (list files, deploy files)
- MicroPico extension only when interactive REPL debugging is needed

## Why This Plan Works
- mpremote is scriptable and stable for deploy/list operations
- MicroPico REPL is useful for manual testing but can lock COM3
- Separating modes prevents Access denied and port in use errors

## Workspace Files Added For This Workflow
- tools/list_pico_files.ps1
- tools/deploy_pico.ps1
- .vscode/tasks.json

## Daily Workflow (Recommended)

### 1) Start in Automation Mode
Keep MicroPico vREPL closed.

### 2) List Files on Pico
Run this task in VS Code:
- Pico: List Files (mpremote)

Or run command directly:
    powershell -ExecutionPolicy Bypass -File tools/list_pico_files.ps1 -Port COM3

### 3) Deploy Project Files to Pico
Run this task in VS Code:
- Pico: Deploy Project Files (mpremote)

Or run command directly:
    powershell -ExecutionPolicy Bypass -File tools/deploy_pico.ps1 -Port COM3

### 4) Optional Interactive Debugging
If you need REPL debugging:
- Open MicroPico vREPL
- Test manually
- Disconnect/close vREPL before using mpremote again

## Deploy Behavior
The deploy script uploads these files:
- config.py
- main.py
- motor.py
- sensorssr04.py
- wifi_car.py
- boot.py (only if a local boot.py exists)

## About boot.py
Current boot.py behavior (LED blink then LED on) is safe and does not disable USB REPL.

A boot.py becomes risky only if it disables USB serial features, such as disabling USB CDC.

## Troubleshooting Guide

### Symptom: mpremote failed to access COM3 (may be in use)
Cause:
- Another app owns COM3 (MicroPico vREPL, Thonny, serial monitor, or stale session)

Fix order:
1. Close MicroPico vREPL
2. Close other serial tools
3. Unplug and replug Pico
4. Retry list/deploy script

### Symptom: Access denied on COM3 from pyserial/mpremote
Cause:
- OS-level COM lock

Fix order:
1. Close VS Code windows
2. Replug Pico
3. Reopen VS Code
4. Run mpremote first before opening vREPL

### Symptom: SyntaxError when running mpremote command
Cause:
- PowerShell command was entered at MicroPython >>> prompt

Fix:
- Run PowerShell commands in a PowerShell terminal only
- Run MicroPython code only at >>> prompt

## Quick Decision Matrix
- Need reliable upload/list now: use mpremote scripts/tasks
- Need live REPL interaction: use MicroPico vREPL
- Need both in one session: switch modes, never concurrently

## Practice Checklist
- I can list Pico files with the list script
- I can deploy all project files with the deploy script
- I know to close vREPL before running mpremote
- I know how to recover from COM3 lock

## Team Convention
For this project, default to mpremote automation.
Open the MicroPico extension only for short, intentional REPL sessions.
