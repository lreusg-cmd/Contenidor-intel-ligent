import paho.mqtt.client as mqtt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import sys

# --- 1. CONFIGURACIÓ GOOGLE SHEETS (Amb la teva clau de profe) ---
# El fitxer JSON de la clau ha d'estar a la mateixa carpeta que aquest script
FITXER_CLAU = "clau-profe.json" 

# --- 2. CADA ALUMNE HA DE CANVIAR AIXÒ ---
# El nom exacte del seu full de càlcul de Google
NOM_FULL_CALCUL = "Dades_Recicla_GrupXX" 

# --- 3. CONFIGURACIÓ MQTT ---
BROKER_IP = "IP_DEL_TEU_BROKER" # La IP del CT-Broker que tu els donis
TOPIC = "contenidor/registre"

def connectar_google():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(FITXER_CLAU, scope)
        client = gspread.authorize(creds)
        return client.open(NOM_FULL_CALCUL).sheet1
    except Exception as e:
        print(f"❌ Error amb Google Sheets: {e}")
        sys.exit()

def on_message(client, userdata, message):
    try:
        # Rebem el missatge (ex: "ID: [1, 2, 3, 4] - Alumne: Marc")
        contingut = message.payload.decode("utf-8")
        data_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        print(f"📩 Dada rebuda: {contingut}")
        
        # Escrivim a la següent fila buida de Google Sheets
        hoja.append_row([data_hora, contingut])
        print(f"✅ Guardat a Google Sheets correctament.")
        
    except Exception as e:
        print(f"❌ Error en guardar: {e}")

# --- INICI DEL PROGRAMA ---
print("🚀 Iniciant el pont de dades...")

# Connectem amb Google
hoja = connectar_google()
print(f"📊 Connectat al full: {NOM_FULL_CALCUL}")

# Connectem amb el Broker MQTT
client_mqtt = mqtt.Client()
client_mqtt.on_message = on_message
client_mqtt.connect(BROKER_IP)
client_mqtt.subscribe(TOPIC)

print(f"📡 Escoltant missatges al tòpic '{TOPIC}'...")
client_mqtt.loop_forever()
