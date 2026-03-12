# mfrc522.py net i robust
from machine import Pin, SoftSPI

class MFRC522:
    OK = 0
    NOTAGERR = 1
    ERR = 2
    REQIDL = 0x26
    ANTICOLL = 0x93

    def __init__(self, spi, gpioRst, gpioCs):
        self.spi = spi
        self.rst = Pin(gpioRst, Pin.OUT)
        self.cs = Pin(gpioCs, Pin.OUT)
        self.cs.value(1)
        self.rst.value(1)
        self.init()

    def _wreg(self, reg, val):
        self.cs.value(0)
        self.spi.write(bytearray([(reg << 1) & 0x7E, val]))
        self.cs.value(1)

    def _rreg(self, reg):
        self.cs.value(0)
        self.spi.write(bytearray([((reg << 1) & 0x7E) | 0x80]))
        val = self.spi.read(1)[0]
        self.cs.value(1)
        return val

    def _tcom(self, cmd, data):
        back_data = []
        back_len = 0
        err = self.OK
        irq_en = 0x00
        wait_irq = 0x00
        if cmd == 0x0E: # Authenticate
            irq_en = 0x12
            wait_irq = 0x10
        elif cmd == 0x0C: # Transceive
            irq_en = 0x77
            wait_irq = 0x30
        self._wreg(0x02, irq_en | 0x80)
        self._clear_bit(0x04, 0x80)
        self._set_bit(0x01, 0x80)
        self._wreg(0x0A, 0x00)
        for i in data: self._wreg(0x09, i)
        self._wreg(0x01, cmd)
        if cmd == 0x0C: self._set_bit(0x0D, 0x80)
        i = 2000
        while True:
            n = self._rreg(0x04)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)): break
        self._clear_bit(0x0D, 0x80)
        if i != 0:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                err = self.OK
                if n & irq_en & 0x01: err = self.NOTAGERR
                if cmd == 0x0C:
                    n = self._rreg(0x0A)
                    last_bits = self._rreg(0x0C) & 0x07
                    if last_bits != 0: back_len = (n - 1) * 8 + last_bits
                    else: back_len = n * 8
                    if n == 0: n = 1
                    if n > 16: n = 16
                    for i in range(n): back_data.append(self._rreg(0x09))
            else: err = self.ERR
        return err, back_data, back_len

    def _set_bit(self, reg, mask): self._wreg(reg, self._rreg(reg) | mask)
    def _clear_bit(self, reg, mask): self._wreg(reg, self._rreg(reg) & (~mask))

    def init(self):
        self.rst.value(0)
        self.rst.value(1)
        self._wreg(0x01, 0x0F) # Reset
        self._wreg(0x2A, 0x8D) # TMode
        self._wreg(0x2B, 0x3E) # TPrescaler
        self._wreg(0x2D, 30)   # TReloadL
        self._wreg(0x2C, 0)    # TReloadH
        self._wreg(0x15, 0x40) # TXASK
        self._wreg(0x11, 0x3D) # Mode
        self.antenna_on()

    def antenna_on(self):
        if ~(self._rreg(0x14) & 0x03): self._set_bit(0x14, 0x03)

    def request(self, mode):
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tcom(0x0C, [mode])
        if (stat != self.OK) | (bits != 0x10): stat = self.ERR
        return stat, bits

    def anticoll(self):
        self._wreg(0x0D, 0x00)
        (stat, recv, bits) = self._tcom(0x0C, [0x93, 0x20])
        if stat == self.OK:
            if len(recv) == 5:
                check = 0
                for i in range(4): check ^= recv[i]
                if check != recv[4]: stat = self.ERR
            else: stat = self.ERR
        return stat, recv

def time_sleep_ms(ms):
    import time
    time.sleep_ms(ms)