import network
import time
from umqtt.simple import MQTTClient
from machine import Pin, SoftSPI, PWM
import mfrc522

# --- 1. CONFIGURACIÓ ---
WIFI_SSID = "Wifi_Aula"
WIFI_PASS = "12345678"
MQTT_BROKER = "192.168.100.28"
TOPIC = "contenidor/registre"

# --- 2. CONFIGURACIÓ HARDWARE ---
led_v = Pin(27, Pin.OUT)
led_r = Pin(25, Pin.OUT)

def moure_servo(posicio):
    try:
        pwm = PWM(Pin(13), freq=50)
        pwm.duty(posicio)
        time.sleep(0.7)
        pwm.duty(0)
        time.sleep_ms(50)
        pwm.deinit()
    except:
        pass

spi = SoftSPI(baudrate=100000, polarity=0, phase=0, 
              sck=Pin(18), mosi=Pin(23), miso=Pin(19))
rdr = mfrc522.MFRC522(spi, gpioRst=22, gpioCs=21)
rdr._wreg(0x26, 0x70)

# --- 3. FUNCIONS DE XARXA ---
def connectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        for i in range(5): 
            if wlan.isconnected(): break
            time.sleep(1)

# --- 4. LÒGICA DE LECTURA AMB TIMEOUT REAL ---
def executa_lectura(id_hex):
    print(f"\n💳 Polsera: {id_hex}")
    
    # 1. ACCIÓ LOCAL (Obrir)
    led_v.value(1)      
    moure_servo(91)     
    inici_ms = time.ticks_ms()

    # 2. INTENT MQTT "SUPER RÀPID"
    # Utilitzem un bloc try molt estricte
    try:
        client = MQTTClient("ESP32_" + str(time.ticks_ms()), MQTT_BROKER, keepalive=2)
        
        # Aquest és el mètode més compatible per forçar el timeout a MicroPython
        import usocket as socket
        # Creem un socket manual per testejar si el port 1883 respon abans de cridar MQTT
        s = socket.socket()
        s.settimeout(0.5) # NOMÉS ESPEREM MIG SEGON
        
        try:
            addr = socket.getaddrinfo(MQTT_BROKER, 1883)[0][-1]
            s.connect(addr)
            s.close()
            # Si el socket s'ha obert, llavors enviem MQTT
            client.connect()
            client.publish(TOPIC, id_hex)
            client.disconnect()
            print("📩 Dada enviada al Broker.")
        except:
            print("❌ Broker no respon (Timeout 0.5s)")
            s.close()
            
    except Exception as e:
        print("❌ Error de xarxa.")

    # 3. AJUST DEL TEMPS (Sempre 5 segons total)
    passat_ms = time.ticks_diff(time.ticks_ms(), inici_ms)
    restant_ms = 5000 - passat_ms
    
    if restant_ms > 0:
        time.sleep_ms(restant_ms)
    
    # 4. TANCAMENT
    moure_servo(40)     
    led_v.value(0)      
    print("🔒 Comporta tancada (5s exactes).")

# --- 5. INICI ---
led_r.value(0) 
led_v.value(0) 
connectar_wifi()
print("\n🚀 SISTEMA A PUNT (Fix de timeout aplicat)...")

while True:
    (stat, tag_type) = rdr.request(rdr.REQIDL)
    if stat == rdr.OK:
        (stat, uid) = rdr.anticoll()
        if stat == rdr.OK:
            id_text = "0x%02x%02x%02x%02x" % (uid[0], uid[1], uid[2], uid[3])
            executa_lectura(id_text)
    time.sleep_ms(100)