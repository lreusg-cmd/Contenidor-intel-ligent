import network
import time
from umqtt.simple import MQTTClient
from machine import Pin, SoftSPI, PWM
import mfrc522

# --- 1. CONFIGURACIÓ ---
WIFI_SSID = "Wifi_Aula"
WIFI_PASS = "12345678"
MQTT_BROKER = "192.168.100.52"
TOPIC = "contenidor/registre"

# --- 2. CONFIGURACIÓ HARDWARE (Els teus pins confirmats) ---
# LEDs
led_v = Pin(27, Pin.OUT)
led_r = Pin(25, Pin.OUT)

# Servo (Pin 13)
def moure_servo(posicio):
    try:
        pwm = PWM(Pin(13), freq=50)
        pwm.duty(posicio)
        time.sleep(1) # Temps perquè el motor es mogui
        pwm.deinit()  # IMPORTANT: Apaguem el pin del servo per no interferir amb el WiFi
    except:
        pass

# RFID (La teva configuració que llegeix bé)
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, 
              sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = mfrc522.MFRC522(spi, gpioRst=22, gpioCs=21)
rdr._wreg(0x26, 0x70)

# --- 3. FUNCIONS ---
def connectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connectant al WiFi...")
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(1)
    print(f"✅ WiFi OK! IP: {wlan.ifconfig()[0]}")

def accio_completa(id_hex):
    # 1. Semàfor Verd immediat
    led_r.value(0)
    led_v.value(1)
    
    # 2. Enviem al Broker
    try:
        client = MQTTClient("ESP32_Aula_" + str(time.ticks_ms()), MQTT_BROKER)
        client.connect()
        client.publish(TOPIC, id_hex)
        client.disconnect()
        print(f"📩 Enviat al Broker: {id_hex}")
    except Exception as e:
        print(f"❌ Error Broker: {e}")

    # 3. Movem el Servo (Obrir)
    moure_servo(115)
    time.sleep(2)
    
    # 4. Tanquem i tornem al vermell
    moure_servo(40)
    led_v.value(0)
    led_r.value(1)

# --- 4. BUCLE PRINCIPAL ---
led_r.value(1) # Iniciem en vermell
led_v.value(0)
connectar_wifi()
print("🚀 SISTEMA INTEGRAT A PUNT...")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()
        if stat == rdr.OK:
            id_text = "0x%02x%02x%02x%02x" % (uid[0], uid[1], uid[2], uid[3])
            print(f"💳 Polsera: {id_text}")
            accio_completa(id_text)
            
    time.sleep_ms(100)