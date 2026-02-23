import subprocess
import sys
import signal
import csv
import os
import time
import glob

# ========= COLORES =========
class C:
    ROJO = "\033[91m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    RESET = "\033[0m"


proceso_actual = None
INTERFAZ = None
REDES = []


# ========= HEADER =========
def header():
    os.system("clear")
    print(C.AZUL + """
╔══════════════════════════════╗
║      WIFI AUDIT PRO CLI      ║
║        Laboratorio           ║
╚══════════════════════════════╝
""" + C.RESET)

def obtener_oui(bssid):
    return ":".join(bssid.upper().split(":")[0:3])

def cargar_ouis():

    ouis = set()

    try:
        with open("bssids.txt") as f:
            for linea in f:
                if linea.strip():
                    oui = linea.split(",")[0].upper()
                    ouis.add(oui)

    except:
        print(C.ROJO + "No se pudo cargar bssids.txt" + C.RESET)

    return ouis


# ========= DETECTAR INTERFACES =========
def detectar_interfaces():

    print(C.AMARILLO + "[*] Detectando interfaces WiFi..." + C.RESET)

    resultado = subprocess.check_output("iw dev", shell=True).decode()

    interfaces = []

    for linea in resultado.split("\n"):
        if "Interface" in linea:
            interfaces.append(linea.split()[1])

    return interfaces


# ========= EJECUTAR COMANDO STREAM =========
def ejecutar_stream(comando):

    global proceso_actual

    try:
        proceso_actual = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        for linea in proceso_actual.stdout:
            print(linea.strip())

        proceso_actual.wait()

    except KeyboardInterrupt:
        detener_proceso()


# ========= DETENER PROCESO =========
def detener_proceso():
    global proceso_actual

    if proceso_actual:
        print(C.ROJO + "\n[!] Cancelando proceso..." + C.RESET)
        proceso_actual.terminate()

def obtener_ultimo_scan():

    archivos = glob.glob("scan-*.csv")

    if not archivos:
        return None

    return max(archivos, key=os.path.getctime)

# ========= ESCANEAR REDES =========
def escanear_redes():

    global REDES

    print(C.AMARILLO + "\n[*] Escaneando redes por 15 segundos...\n" + C.RESET)

    comando = [
        "airodump-ng",
        "--output-format", "csv",
        "-w", "scan", "--manufacturer",
        INTERFAZ
    ]

    proc = subprocess.Popen(comando)

    time.sleep(15)
    proc.terminate()

    REDES.clear()

    archivo = obtener_ultimo_scan()

    if not archivo:
        print("No se encontró archivo scan")
        return

    ouis_validos = cargar_ouis()

    try:
        with open(archivo, newline='', encoding='latin-1') as csvfile:
            lector = csv.reader(csvfile)

            for fila in lector:

                if len(fila) > 13 and fila[0] != "BSSID":

                    bssid = fila[0].strip()
                    canal = fila[3].strip()
                    essid = fila[13].strip()

                    oui = obtener_oui(bssid)

                    if oui in ouis_validos:

                        REDES.append({
                            "bssid": bssid,
                            "canal": canal,
                            "essid": essid,
                            "oui": oui
                        })

    except:
        print(C.ROJO + "No se pudo leer resultados" + C.RESET)



# ========= MOSTRAR REDES =========
def mostrar_redes():

    if not REDES:
        print(C.ROJO + "No hay redes cargadas" + C.RESET)
        return

    print("\nID   BSSID              CANAL   OUI       ESSID")
    print("------------------------------------------------------")

    for i, red in enumerate(REDES):
        print(f"{i+1:<4} {red['bssid']:<18} {red['canal']:<7} {red['oui']:<9} {red['essid']}")



# ========= EJECUTAR SCRIPT EXTERNO =========
def ejecutar_prueba(red):

    print(C.VERDE + f"\n[+] Ejecutando prueba sobre {red['essid']}\n" + C.RESET)

    comando = [
        "python3",
        "-u",
        "script_audit.py",
        INTERFAZ,
        red["bssid"]
    ]

    ejecutar_stream(comando)


# ========= SELECCIONAR RED =========
def seleccionar_red():

    mostrar_redes()

    try:
        op = int(input("\nSelecciona red ID: "))
        return REDES[op-1]
    except:
        print("Selección inválida")
        return None


# ========= MENU PRINCIPAL =========
def menu():

    global INTERFAZ

    while True:

        header()

        print("Interfaz actual:", INTERFAZ)
        print("""
1) Seleccionar interfaz
2) Escanear redes
3) Mostrar redes
4) Ejecutar prueba laboratorio
5) Salir
""")

        op = input("Opción: ")

        if op == "1":

            interfaces = detectar_interfaces()

            for i, iface in enumerate(interfaces):
                print(f"{i+1}) {iface}")

            sel = int(input("Selecciona: "))
            INTERFAZ = interfaces[sel-1]

        elif op == "2":

            if not INTERFAZ:
                print("Selecciona interfaz primero")
                input("ENTER...")
                continue

            escanear_redes()
            input("\nEscaneo finalizado ENTER...")

        elif op == "3":
            mostrar_redes()
            input("\nENTER...")

        elif op == "4":

            if not REDES:
                print("Escanea primero")
                input("ENTER...")
                continue

            red = seleccionar_red()

            if red:
                ejecutar_prueba(red)
                input("\nProceso finalizado ENTER...")

        elif op == "5":
            sys.exit()


# ========= CTRL+C =========
signal.signal(signal.SIGINT, lambda s, f: detener_proceso())

if __name__ == "__main__":
    menu()
