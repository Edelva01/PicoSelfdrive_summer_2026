import time
from machine import Pin, PWM, ADC, I2C
from lcd1602 import LCD

i = None


_lcd1602 = None
def _lcd1602_setup(sda, scl):
    global _lcd1602
    i2c = I2C(0, sda=Pin(int(sda)), scl=Pin(int(scl)), freq=100000)
    _lcd1602 = LCD(i2c)
def _lcd1602_clear():
    if _lcd1602 is None:
        raise RuntimeError('Call LCD setup before LCD clear')
    _lcd1602.clear()
def _lcd1602_write(col, row, text):
    if _lcd1602 is None:
        raise RuntimeError('Call LCD setup before LCD write')
    _lcd1602.write(int(col), int(row), str(text))

def main():
  global i
  _lcd1602_setup(0, 1)
  while True:
    _lcd1602_clear()
    _lcd1602_write(0, 0, "Hello, My name's")
    _lcd1602_write(0, 1, 'Lukas Rouse')
    time.sleep_ms(2000)
    _lcd1602_clear()
    _lcd1602_write(0, 0, 'I Love Robots')
    time.sleep_ms(2000)
    _lcd1602_clear()
    _lcd1602_write(0, 0, 'One day, I will ')
    _lcd1602_write(0, 1, 'work at ...')
    time.sleep_ms(4000)
    _lcd1602_clear()
    for count in range(3):
      for i in range(0, 11, 2):
        _lcd1602_clear()
        _lcd1602_write(i, 0, 'NASA')
        time.sleep_ms(500)
        _lcd1602_clear()
        _lcd1602_write((i + 1), 1, 'NASA')
        time.sleep_ms(500)

if __name__ == '__main__':
  main()