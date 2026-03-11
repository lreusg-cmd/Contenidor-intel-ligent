from machine import Pin, PWM, SoftSPI
import time
import mfrc522
from umqtt.simple import MQTTClient

# --- 1. CONFIGURACIÓ WIFI I BROKER ---
WIFI_SSID = "WiFi-Recicla-Aula"
WIFI_PASS = "LaTevaContrasenya"
MQTT_BROKER = "192.168.1.XXX" # IP del teu CT-Broker
CLIENT_ID = "ESP32_Contenidor_01"
TOPIC = "contenidor/registre"

# --- 2. CONFIGURACIÓ HARDWARE ---
# Semàfor
led_v = Pin(27, Pin.OUT)
led_r = Pin(25, Pin.OUT)
# Servo
servo = PWM(Pin(13), freq=50)
# RFID
spi = SoftSPI(baudrate=1000000, polarity=0, phase=0, sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = mfrc522.MFRC522(spi, gpioRst=22, gpioCs=21)

# --- 3. FUNCIONS ---
def connectar_wifi():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    while not wlan.isconnected():
        time.sleep(1)
    print("WiFi OK")

def obrir_contenidor():
    led_r.value(0)   # Apaga vermell
    led_v.value(1)   # Encén verd
    servo.duty(115)  # Obre porta
    time.sleep(3)    # Espera 3 segons
    servo.duty(40)   # Tanca porta
    led_v.value(0)   # Apaga verd
    led_r.value(1)   # Torna al vermell

# --- 4. EXECUCIÓ INICIAL ---
connectar_wifi()
led_r.value(1)  # Comença en vermell
led_v.value(0)
servo.duty(40)  # Porta tancada

print("SISTEMA ACTIU - Esperant polsera...")

# --- 5. BUCLE PRINCIPAL ---
while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()
        if stat == rdr.OK:
            id_polsera = str(uid)
            print("Polsera detectada:", id_polsera)
            
            # ENVIAR AL BROKER (Núvol)
            try:
                client = MQTTClient(CLIENT_ID, MQTT_BROKER)
                client.connect()
                client.publish(TOPIC, "Alumne ID: " + id_polsera)
                client.disconnect()
                print("Dada enviada al Broker")
            except:
                print("Error enviant al Broker")
            
            # ACCIÓ FÍSICA
            obrir_contenidor()
