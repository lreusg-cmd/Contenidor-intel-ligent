import network
import time
from umqtt.simple import MQTTClient

# 1. CONFIGURACIÓ DEL WIFI (Que posin les dades del centre)
WIFI_SSID = "NOM_DE_LA_TEVA_XARXA"
WIFI_PASS = "CONTRASENYA_DEL_WIFI"

# 2. CONFIGURACIÓ DEL BROKER (El teu contenidor Proxmox)
# Els alumnes han de canviar aquesta IP per la del teu CT-Broker
MQTT_BROKER = "192.168.1.XXX" 
CLIENT_ID   = "ESP32_Alumne_1"
TOPIC       = "contenidor/registre"

def connectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    
    print("Connectant al WiFi...", end="")
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(1)
    print("\n✅ WiFi Connectat!")
    print("IP de la placa:", wlan.ifconfig()[0])

def enviar_missatge():
    try:
        client = MQTTClient(CLIENT_ID, MQTT_BROKER)
        client.connect()
        print(f"✅ Connectat al Broker MQTT: {MQTT_BROKER}")
        
        # Enviem un missatge de prova
        missatge = "Hola des de l'ESP32!"
        client.publish(TOPIC, missatge)
        print(f"📩 Missatge enviat al tòpic '{TOPIC}': {missatge}")
        
        client.disconnect()
    except Exception as e:
        print(f"❌ Error connectant al Broker: {e}")

# --- EXECUCIÓ ---
connectar_wifi()
enviar_missatge()
