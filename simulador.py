from machine import Pin, PWM, SoftSPI
import time
import mfrc522 

# --- 1. CONFIGURACIÓ DE PINS ---
led_v = Pin(27, Pin.OUT)
led_g = Pin(26, Pin.OUT) # Groc
led_r = Pin(25, Pin.OUT)

servo = PWM(Pin(13), freq=50)

# Lector RFID (SPI)
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, 
              sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = mfrc522.MFRC522(spi, gpioRst=22, gpioCs=21)

# --- 2. TEST DEL SEMÀFOR ---
print(">>> Pas 1: Provant Semàfor...")
for led in [led_v, led_g, led_r]:
    led.value(1)
    time.sleep(0.5)
    led.value(0)
print("✅ Semàfor OK")

# --- 3. TEST DEL SERVO ---
print(">>> Pas 2: Provant Servo (Porta)...")
servo.duty(40)  
time.sleep(1)
servo.duty(115) 
time.sleep(1)
servo.duty(40)  
print("✅ Servo OK")

# --- 4. TEST DEL LECTOR RFID ---
print(">>> Pas 3: Esperant polsera...")
# Forcem el guany d'antena per si de cas
rdr.init()
rdr._wreg(0x26, 0x70) 

print("Apropa la polsera al lector RFID ara!")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()
        if stat == rdr.OK:
            print("---------------------------")
            # Format correcte per imprimir l'ID en hexadecimal
            id_hex = "".join([hex(x)[2:] for x in uid])
            print("✅ ID DETECTAT: " + id_hex)
            print("---------------------------")
            
            led_v.value(1)
            time.sleep(2)
            led_v.value(0)
            break 
    time.sleep_ms(100)

print(">>> TEST FINALITZAT.")
