from machine import Pin, SoftSPI

class MFRC522:
    OK = 0
    NOTAGERR = 1
    ERR = 2

    REQIDL = 0x26
    REQALL = 0x52
    AUTHENT1A = 0x60
    AUTHENT1B = 0x61

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

    def _set_bitmask(self, reg, mask):
        self._wreg(reg, self._rreg(reg) | mask)

    def _clear_bitmask(self, reg, mask):
        self._wreg(reg, self._rreg(reg) & (~mask))

    def _tcom(self, cmd, send):
        recv = []
        bits = irq = wait = last_bits = 0
        if cmd == 0x0E: irq = 0x12; wait = 0x10
        elif cmd == 0x0C: irq = 0x77; wait = 0x30
        self._wreg(0x04, irq | 0x80)
        self._clear_bitmask(0x05, 0x80)
        self._set_bitmask(0x02, 0x80)
        self._wreg(0x01, 0x00)
        for i in range(len(send)): self._wreg(0x09, send[i])
        self._wreg(0x01, cmd)
        if cmd == 0x0C: self._set_bitmask(0x0D, 0x80)
        i = 2000
        while True:
            n = self._rreg(0x05)
            i -= 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait)): break
        self._clear_bitmask(0x0D, 0x80)
        if i != 0:
            if (self._rreg(0x06) & 0x1B) == 0x00:
                if n & irq:
                    if cmd == 0x0C:
                        n = self._rreg(0x0A)
                        last_bits = self._rreg(0x0C) & 0x07
                        if last_bits != 0: bits = (n - 1) * 8 + last_bits
                        else: bits = n * 8
                        if n == 0: n = 1
                        if n > 16: n = 16
                        for _ in range(n): recv.append(self._rreg(0x09))
            else: return self.ERR, recv, bits
        return self.OK, recv, bits

    def init(self):
        self.rst.value(0)
        time_sleep_ms(1)
        self.rst.value(1)
        time_sleep_ms(1)
        self._wreg(0x11, 0x3D)
        self._wreg(0x2D, 0x1E)
        self._wreg(0x2C, 0x00)
        self._wreg(0x2B, 0x0A)
        self._wreg(0x15, 0x40)
        self._wreg(0x11, 0x3D)
        self.antenna_on()

    def antenna_on(self, on=True):
        if on and ~(self._rreg(0x14) & 0x03): self._set_bitmask(0x14, 0x03)
        else: self._clear_bitmask(0x14, 0x03)

    def request(self, mode):
        self._wreg(0x0D, 0x07)
        (stat, recv, bits) = self._tcom(0x0C, [mode])
        if (stat != self.OK) or (bits != 0x10): stat = self.ERR
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

    def select_tag(self, ser):
        buf = [0x93, 0x70] + ser[0:5]
        (stat, recv, bits) = self._tcom(0x0C, buf)
        return self.OK if (stat == self.OK) and (bits == 0x18) else self.ERR

def time_sleep_ms(ms):
    import time
    time.sleep_ms(ms)
