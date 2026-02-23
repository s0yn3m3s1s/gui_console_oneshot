import sys
import subprocess

iface = sys.argv[1]
bssid = sys.argv[2]

print("Interfaz:", iface)
print("Objetivo:", bssid)

# AQUÍ conectas tu herramienta de auditoría autorizada
comando = ["python3", "oneshot.py","-i",iface,"-b",bssid,"-K"]

proceso = subprocess.Popen(
    comando,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

for linea in proceso.stdout:
    print(linea.strip())

proceso.wait()
