from machine import Pin, SoftSPI
import mfrc522
import time

# Configura SPI a només 100kHz per evitar soroll
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, 
              sck=Pin(18), mosi=Pin(23), miso=Pin(19))

rdr = mfrc522.MFRC522(spi, gpioRst=22, gpioCs=21)

# Posa el guany de l'antena al màxim
rdr._wreg(0x26, 0x70)

print(">>> TEST DE LECTURA (Fes servir el clauer blau)")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()
        if stat == rdr.OK:
            print("✅ TROBAT! ID:", [hex(x) for x in uid])
            time.sleep(1)
    time.sleep_ms(100)
