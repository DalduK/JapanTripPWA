#!/usr/bin/env python3
"""
🌸 PWA DEV SERVER — HTTPS + iPhone ready
Uruchom:
    python serve.py
"""

import http.server
import ssl
import subprocess
import os
import sys
import socket
import qrcode

PORT = 8443
DIR = os.path.dirname(os.path.abspath(__file__))

CERT = os.path.join(DIR, "cert.pem")
KEY = os.path.join(DIR, "key.pem")


# ─────────────────────────────────────────────
# LOCAL IP
# ─────────────────────────────────────────────
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# ─────────────────────────────────────────────
# OPENSSL AUTO DETECT
# ─────────────────────────────────────────────
def find_openssl():
    try:
        subprocess.run(
            ["openssl", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return "openssl"
    except FileNotFoundError:
        pass

    paths = [
        r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
        r"C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe",
    ]

    for p in paths:
        if os.path.exists(p):
            return p

    print("❌ OpenSSL nie znaleziony.")
    sys.exit(1)


OPENSSL = find_openssl()


# ─────────────────────────────────────────────
# CERT GENERATION
# ─────────────────────────────────────────────
def gen_cert(ip):
    print(f"🔐 Generuję certyfikat dla {ip}")

    cfg = f"""
[req]
distinguished_name=req
x509_extensions=v3_req
prompt=no

[req_distinguished_name]
CN=PWADEV

[v3_req]
subjectAltName=IP:{ip},IP:127.0.0.1
"""

    cfg_path = os.path.join(DIR, "_ssl.cfg")
    with open(cfg_path, "w") as f:
        f.write(cfg)

    subprocess.run([
        OPENSSL,
        "req",
        "-x509",
        "-newkey",
        "rsa:2048",
        "-nodes",
        "-days",
        "365",
        "-keyout",
        KEY,
        "-out",
        CERT,
        "-config",
        cfg_path
    ])

    os.remove(cfg_path)
    print("✅ Cert wygenerowany")


# ─────────────────────────────────────────────
# HTTP HANDLER (PWA friendly)
# ─────────────────────────────────────────────
class Handler(http.server.SimpleHTTPRequestHandler):

    START_FILE = "japan-plan.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    # 🔒 blokada listy plików
    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None

    # 🎯 root → twoja aplikacja
    def do_GET(self):
        if self.path == "/" or self.path == "":
            self.path = "/" + self.START_FILE

        return super().do_GET()

    # headers dobre dla PWA dev
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, *args):
        pass


# ─────────────────────────────────────────────
# START
# ─────────────────────────────────────────────
IP = get_local_ip()

if not (os.path.exists(CERT) and os.path.exists(KEY)):
    gen_cert(IP)

httpd = http.server.HTTPServer(("0.0.0.0", PORT), Handler)

ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ctx.load_cert_chain(CERT, KEY)

httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)

URL = f"https://{IP}:{PORT}/"

print("\n🌸 PWA DEV SERVER RUNNING")
print("====================================")
print("URL:", URL)
print("====================================\n")

# QR CODE (🔥 mega wygodne)
try:
    qr = qrcode.QRCode(border=1)
    qr.add_data(URL)
    qr.make(fit=True)
    qr.print_ascii(invert=True)
except Exception:
    img = qrcode.make(URL)
    img.save("qr.png")
    print("📱 QR zapisany jako qr.png")

print("\n📱 Zeskanuj QR i otwórz w Safari")
print("Dodaj do ekranu głównego → test PWA\n")

try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\n👋 Server stopped")