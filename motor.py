from machine import Pin
import config

left_bi = Pin(config.LEFT_BI, Pin.OUT)
left_fi = Pin(config.LEFT_FI, Pin.OUT)

def stop():
    left_bi.value(0)
    left_fi.value(0)

def forward():
    left_bi.value(0)
    left_fi.value(1)

def backward():
    left_bi.value(1)
    left_fi.value(0)

def left():
    # Temporary until I have driver
    left_bi.value(1)
    left_fi.value(0)

def right():
    #Temporary until I have driver
    left_bi.value(0)
    left_fi.value(1)