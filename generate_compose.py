#!/usr/bin/env python3
"""
UAM StreamApps — Generador de docker-compose.yml y nginx.conf
Lee la cantidad de contenedores de config.json y genera los archivos de orquestación.

Uso:
    python3 generate_compose.py          # Lee config.json del directorio actual
    python3 generate_compose.py 10       # Override: genera para 10 contenedores
"""

import json
import sys
import base64
import os

# --- Leer configuración ---
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Cantidad de contenedores (override por argumento o desde config)
if len(sys.argv) > 1:
    NUM = int(sys.argv[1])
else:
    NUM = config.get("contenedores", {}).get("cantidad", 25)

VNC_PW = config.get("contenedores", {}).get("vnc", {}).get("password", "Mayab2026")
LSEG_URL = config.get("lseg_refinitiv", {}).get("url", "https://workspace.refinitiv.com")
PROXY_PORT_BASE = 8901

# BasicAuth header para Nginx
auth_b64 = base64.b64encode(f"kasm_user:{VNC_PW}".encode()).decode()
AUTH_HEADER = f"Basic {auth_b64}"

print(f"Generando para {NUM} contenedores...")
print(f"VNC Password: {'*' * len(VNC_PW)}")
print(f"Proxy ports: {PROXY_PORT_BASE}-{PROXY_PORT_BASE + NUM - 1}")

# ============================================================
# 1. Generar docker-compose.yml
# ============================================================
dc = []
dc.append(f"# ===== UAM StreamApps — Docker Compose ({NUM} contenedores) =====")
dc.append(f"# Generado automáticamente por generate_compose.py")
dc.append(f"# Para regenerar: python3 generate_compose.py")
dc.append("")
dc.append("# Configuración común Kasm (YAML anchor)")
dc.append("x-kasm-defaults: &kasm_defaults")
dc.append("  image: uam-streamapps-kasm:latest")
dc.append("  platform: linux/amd64")
dc.append("  restart: unless-stopped")
dc.append('  shm_size: "2gb"')
dc.append("  cap_add:")
dc.append("    - SYS_ADMIN")
dc.append("  dns:")
dc.append("    - 8.8.8.8")
dc.append("    - 8.8.4.4")
dc.append("    - 1.1.1.1")
dc.append("  environment:")
dc.append(f'    VNC_PW: "{VNC_PW}"')
dc.append(f'    LAUNCH_URL: "{LSEG_URL}"')
dc.append('    KASM_SVC_AUDIO: "0"')
dc.append('    KASM_SVC_AUDIO_INPUT: "0"')
dc.append("")
dc.append("services:")
dc.append("")
dc.append("  # --- Portal Web ---")
dc.append("  portal:")
dc.append("    build: ./portal")
dc.append("    container_name: uam_portal")
dc.append("    ports:")
dc.append('      - "8090:8080"')
dc.append("    volumes:")
dc.append("      - ./config.json:/app/config.json:ro")
dc.append("    env_file: .env")
dc.append("    restart: unless-stopped")
dc.append("")
dc.append("  # --- Nginx Reverse Proxy (SSL + BasicAuth) ---")
dc.append("  nginx:")
dc.append("    build: ./nginx")
dc.append("    container_name: uam_nginx")
dc.append("    ports:")
dc.append('      - "443:443"')
for i in range(1, NUM + 1):
    port = PROXY_PORT_BASE + i - 1
    dc.append(f'      - "{port}:{port}"')
dc.append("    restart: unless-stopped")
dc.append("")
dc.append(f"  # --- Contenedores Kasm (01-{NUM:02d}) ---")

for i in range(1, NUM + 1):
    dc.append(f"  kasm_{i:02d}:")
    dc.append("    <<: *kasm_defaults")
    dc.append(f"    container_name: kasm_{i:02d}")
    dc.append("    ports:")
    dc.append(f'      - "{6900 + i}:6901"')
    dc.append("    volumes:")
    dc.append(f"      - kasm_chrome_{i:02d}:/opt/chrome-data")
    dc.append("")

dc.append("# --- Volúmenes ---")
dc.append("volumes:")
for i in range(1, NUM + 1):
    dc.append(f"  kasm_chrome_{i:02d}:")

compose_content = "\n".join(dc)

# ============================================================
# 2. Generar nginx/nginx.conf
# ============================================================
ng = []
ng.append(f"# ===== Nginx Reverse Proxy — UAM StreamApps ({NUM} contenedores) =====")
ng.append("# Generado automáticamente por generate_compose.py")
ng.append("")
ng.append("events {")
ng.append("    worker_connections 1024;")
ng.append("}")
ng.append("")
ng.append("http {")
ng.append("    proxy_read_timeout 86400s;")
ng.append("    proxy_send_timeout 86400s;")
ng.append("    proxy_connect_timeout 7s;")
ng.append("")
ng.append("    map $http_upgrade $connection_upgrade {")
ng.append("        default upgrade;")
ng.append("        '' close;")
ng.append("    }")
ng.append("")

for i in range(1, NUM + 1):
    port = PROXY_PORT_BASE + i - 1
    ng.append(f"    # --- Kasm {i:02d} (puerto {port}) ---")
    ng.append(f"    server {{")
    ng.append(f"        listen {port} ssl;")
    ng.append(f"        server_name _;")
    ng.append(f"        ssl_certificate /etc/nginx/ssl/cert.pem;")
    ng.append(f"        ssl_certificate_key /etc/nginx/ssl/key.pem;")
    ng.append(f"        proxy_buffering off;")
    ng.append(f"        location / {{")
    ng.append(f"            proxy_pass https://kasm_{i:02d}:6901;")
    ng.append(f'            proxy_set_header Authorization "{AUTH_HEADER}";')
    ng.append(f"            proxy_set_header Host $host;")
    ng.append(f"            proxy_set_header X-Real-IP $remote_addr;")
    ng.append(f"            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
    ng.append(f"            proxy_set_header X-Forwarded-Proto $scheme;")
    ng.append(f"            proxy_http_version 1.1;")
    ng.append(f"            proxy_set_header Upgrade $http_upgrade;")
    ng.append(f"            proxy_set_header Connection $connection_upgrade;")
    ng.append(f"            proxy_ssl_verify off;")
    ng.append(f"        }}")
    ng.append(f"    }}")
    ng.append("")

# Portal HTTPS
ng.append("    # --- Portal Web (HTTPS) ---")
ng.append("    server {")
ng.append("        listen 443 ssl;")
ng.append("        server_name _;")
ng.append("        ssl_certificate /etc/nginx/ssl/cert.pem;")
ng.append("        ssl_certificate_key /etc/nginx/ssl/key.pem;")
ng.append("        location / {")
ng.append("            proxy_pass http://portal:8080;")
ng.append("            proxy_set_header Host $host;")
ng.append("            proxy_set_header X-Real-IP $remote_addr;")
ng.append("            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;")
ng.append("            proxy_set_header X-Forwarded-Proto https;")
ng.append("            proxy_http_version 1.1;")
ng.append("            proxy_set_header Upgrade $http_upgrade;")
ng.append("            proxy_set_header Connection $connection_upgrade;")
ng.append("        }")
ng.append("    }")
ng.append("")
ng.append("}")

nginx_content = "\n".join(ng)

# ============================================================
# 3. Escribir archivos
# ============================================================
script_dir = os.path.dirname(os.path.abspath(__file__))

compose_path = os.path.join(script_dir, "docker-compose.yml")
with open(compose_path, "w", encoding="utf-8") as f:
    f.write(compose_content)
print(f"✅ docker-compose.yml ({len(compose_content)} chars)")

nginx_path = os.path.join(script_dir, "nginx", "nginx.conf")
with open(nginx_path, "w", encoding="utf-8") as f:
    f.write(nginx_content)
print(f"✅ nginx/nginx.conf ({len(nginx_content)} chars)")

print(f"\n🚀 Listo. Ejecuta (en este orden):")
print(f"   # 1. Construir la imagen Kasm UNA sola vez (compartida por los {NUM} contenedores)")
print(f"   docker build -f Dockerfile.kasm -t uam-streamapps-kasm:latest .")
print(f"   # 2. Construir portal + nginx y levantar todo")
print(f"   docker compose build")
print(f"   docker compose up -d")
print(f"\n📊 Puertos:")
print(f"   Portal HTTP:  8090")
print(f"   Portal HTTPS: 443")
print(f"   Kasm proxy:   {PROXY_PORT_BASE}-{PROXY_PORT_BASE + NUM - 1}")
print(f"   Kasm directo: 6901-{6900 + NUM}")
