from machine import Pin, PWM, SoftSPI
import time
import mfrc522

# --- 1. CONFIGURACIÓ HARDWARE ---
# Semàfor
led_v = Pin(27, Pin.OUT)
led_r = Pin(25, Pin.OUT)

# Servo
servo = PWM(Pin(13), freq=50)

# Lector RFID (SPI)
spi = SoftSPI(baudrate=1000000, polarity=0, phase=0, 
              sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = mfrc522.MFRC522(spi, gpioRst=22, gpioCs=21)

# --- 2. FUNCIONS D'ACCIÓ ---
def obrir_porta():
    print("🔓 Polsera correcte! Obrint...")
    led_r.value(0)   # Apaguem vermell
    led_v.value(1)   # Encenem verd
    
    servo.duty(115)  # Girem servo (Obert)
    time.sleep(3)    # Esperem 3 segons per llençar el residu
    
    servo.duty(40)   # Girem servo (Tancat)
    led_v.value(0)   # Apaguem verd
    led_r.value(1)   # Tornem al vermell (Repòs)
    print("🔒 Porta tancada. Esperant següent...")

# --- 3. ESTAT INICIAL ---
led_r.value(1)   # Comença en vermell
led_v.value(0)   # Verd apagat
servo.duty(40)   # Porta tancada
print("🚀 Sistema a punt. Apropa la polsera...")

# --- 4. BUCLE PRINCIPAL ---
while True:
    # El lector busca si hi ha alguna targeta a prop
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    
    if stat == rdr.OK:
        # Si troba una, n'extreu l'ID (anticol·lisió)
        (stat, uid) = rdr.anticoll()
        
        if stat == rdr.OK:
            print("ID Detectat:", uid)
            obrir_porta()