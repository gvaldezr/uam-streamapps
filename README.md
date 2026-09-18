# UAM StreamApps - Portal de Acceso a Refinitiv Workspace

## 📋 Descripción

**UAM StreamApps** es un sistema innovador que permite servir Refinitiv Workspace a los alumnos de la Universidad Anáhuac Mayab de forma segura y sin necesidad de compartir las credenciales del software.

El proyecto utiliza contenedores Docker con **KasmVNC** y **Google Chrome** para proporcionar sesiones de escritorio virtuales individuales, garantizando:

- ✅ Aislamiento de credenciales (cada alumno tiene su propia sesión)
- ✅ Acceso simultáneo de múltiples usuarios sin interferencias
- ✅ Interfaz web intuitiva para inicio de sesión
- ✅ Dashboard de supervisión para profesores
- ✅ Escalabilidad hasta 25 sesiones concurrentes
- ✅ Fácil gestión de horarios y clases

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│                   ALUMNOS / PROFESORES                        │
│                   (Navegadores Web)                           │
│                                                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ HTTP/HTTPS
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                                                               │
│              PORTAL DE ACCESO (Puerto 8080)                   │
│         (Node.js/Express - Autenticación)                    │
│                                                               │
│  - Validación de usuarios de clases                          │
│  - Gestión de sesiones                                       │
│  - Dashboard de supervisión (profesores)                     │
│                                                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    (Puerto 6901)  (Puerto 6902) (Puerto 6903-6925)
         │             │             │
┌────────▼────┐  ┌─────▼────┐  ┌────▼─────────┐
│  Contenedor  │  │Contenedor │  │  Contenedor  │
│  KasmVNC #1  │  │ KasmVNC #2│  │  KasmVNC #N  │
│              │  │           │  │              │
│ ┌──────────┐ │  │┌────────┐ │  │ ┌──────────┐ │
│ │  Chrome  │ │  ││Chrome  │ │  │ │  Chrome  │ │
│ │┌────────┐│ │  │└────────┘ │  │ └──────────┘ │
│ ││Refinitiv││ │  │┌────────┐ │  │ ┌──────────┐ │
│ ││Workspace││ │  ││Refinitiv│ │  │ │Refinitiv │ │
│ │└────────┘│ │  ││Workspace│ │  │ │Workspace │ │
│ └──────────┘ │  │└────────┘ │  │ └──────────┘ │
│              │  │           │  │              │
└──────────────┘  └───────────┘  └──────────────┘

┌──────────────────────────────────────────────────────────────┐
│                   INFRAESTRUCTURA                             │
│  Docker Engine • Docker Compose • Sistema de Archivos        │
│  Red Docker • Volúmenes Persistentes                         │
└──────────────────────────────────────────────────────────────┘
```

---

## 💻 Requisitos Previos

Antes de instalar UAM StreamApps, asegúrate de contar con lo siguiente:

### Hardware Mínimo Requerido

| Componente | Requisito |
|-----------|-----------|
| **CPU** | 8+ núcleos (recomendado 16+) |
| **RAM** | **64GB mínimo** para 25 contenedores (2.5GB por contenedor) |
| **Disco Duro** | **100GB SSD** mínimo (10GB SO + 80GB contenedores + 10GB espacio buffer) |
| **Conexión de Red** | Gigabit Ethernet (recomendado) |

### Software Requerido

- **Docker** v20.10 o superior
- **Docker Compose** v2.0 o superior
- **Sistema Operativo**: macOS 11+, Ubuntu 20.04 LTS+, Debian 11+, CentOS 8+
- **Git** (opcional, para clonar el proyecto)
- **curl** o **wget** (para descargas)

### Verificar Requisitos Previos

```bash
# Verificar Docker
docker --version
# Esperado: Docker version 20.10.x o superior

# Verificar Docker Compose
docker compose version
# Esperado: Docker Compose version 2.x.x o superior

# Verificar RAM disponible
free -h
# Debes ver al menos 64GB disponibles

# Verificar espacio en disco
df -h /
# Debes ver al menos 100GB disponibles
```

### Puertos Requeridos

Asegúrate de que los siguientes puertos no estén en uso:

- **8080**: Portal web de acceso
- **6901-6925**: Contenedores KasmVNC (25 puertos)
- **3306** (opcional): Base de datos MariaDB (si se usa)

---

## 🚀 Instalación

### Paso 1: Clonar/Copiar el Proyecto

```bash
# Opción A: Clonar desde repositorio Git
git clone https://github.com/tuorganizacion/uam-streamapps.git
cd uam-streamapps

# Opción B: Copiar archivos manualmente
# Asegúrate de que tengas la estructura completa del proyecto
ls -la
# Deberías ver: docker-compose.yml, Dockerfile, config.json, .env, etc.
```

### Paso 2: Configurar Variables de Entorno

Edita el archivo `.env` con tus parámetros específicos:

```bash
cp .env.example .env
nano .env  # o usa tu editor preferido
```

Contenido de `.env`:

```env
# Configuración del Portal
PORTAL_HOST=0.0.0.0
PORTAL_PORT=8080
PORTAL_SECRET_KEY=tu_clave_secreta_muy_larga_y_segura_aqui

# Configuración de Docker
COMPOSE_PROJECT_NAME=uam-streamapps
KASM_PORT_START=6901

# Rutas
VOLUMES_DIR=/data/uam-streamapps
CONFIG_FILE=./config.json

# Base de datos (opcional)
MYSQL_ROOT_PASSWORD=password_seguro_aqui
MYSQL_DATABASE=uam_streamapps
MYSQL_USER=uam_user
MYSQL_PASSWORD=password_seguro_aqui

# Refinitiv (credenciales compartidas a nivel backend)
REFINITIV_USERNAME=tu_usuario_refinitiv
REFINITIV_PASSWORD=tu_password_refinitiv

# Configuración de Red
EXTERNAL_URL=http://192.168.1.100:8080
# O usa el dominio si tienes uno:
# EXTERNAL_URL=https://streamapps.tuuniversidad.edu
```

### Paso 3: Configurar Clases y Horarios

Edita `config.json` con la información de tus clases:

```json
{
  "portal": {
    "title": "UAM StreamApps - Refinitiv Workspace",
    "logo_url": "/static/images/logo-uam.png",
    "theme": "light"
  },
  "clases": [
    {
      "id": "clase-001",
      "nombre": "Matemáticas Financieras - Grupo A",
      "profesor": "Dr. Juan García",
      "codigo": "MF-401-A",
      "horarios": [
        {
          "dia": "lunes",
          "inicio": "09:00",
          "fin": "11:00"
        },
        {
          "dia": "miércoles",
          "inicio": "09:00",
          "fin": "11:00"
        }
      ],
      "alumnos": [
        {
          "id": "alumno_001",
          "nombre": "Carlos López",
          "matricula": "AL202401",
          "usuario": "clopez",
          "password": "GeneradoAutomaticamente123!"
        },
        {
          "id": "alumno_002",
          "nombre": "María González",
          "matricula": "AL202402",
          "usuario": "mgonzalez",
          "password": "GeneradoAutomaticamente456!"
        }
      ],
      "max_sesiones": 25,
      "contenedor_prefix": "kasm-clase-001"
    },
    {
      "id": "clase-002",
      "nombre": "Análisis Técnico - Grupo B",
      "profesor": "Dra. Rosa Martínez",
      "codigo": "AT-302-B",
      "horarios": [
        {
          "dia": "martes",
          "inicio": "14:00",
          "fin": "16:00"
        },
        {
          "dia": "jueves",
          "inicio": "14:00",
          "fin": "16:00"
        }
      ],
      "alumnos": [
        {
          "id": "alumno_003",
          "nombre": "Pedro Sánchez",
          "matricula": "AL202403",
          "usuario": "psanchez",
          "password": "GeneradoAutomaticamente789!"
        }
      ],
      "max_sesiones": 15,
      "contenedor_prefix": "kasm-clase-002"
    }
  ],
  "profesores": [
    {
      "id": "prof_001",
      "nombre": "Dr. Juan García",
      "usuario": "jgarcia",
      "password": "PasswordSeguroProfesor001!",
      "clases": ["clase-001"]
    },
    {
      "id": "prof_002",
      "nombre": "Dra. Rosa Martínez",
      "usuario": "rmartinez",
      "password": "PasswordSeguroProfesor002!",
      "clases": ["clase-002"]
    }
  ],
  "administradores": [
    {
      "usuario": "admin",
      "password": "PasswordSeguroAdmin123!"
    }
  ],
  "kasm": {
    "puerto_inicio": 6901,
    "imagen": "kasmweb/kasm-ubuntu:develop",
    "memoria_por_contenedor": "2.5G",
    "cpus_por_contenedor": 2,
    "timeout_sesion": 3600,
    "timeout_inactividad": 1800
  },
  "refinitiv": {
    "auto_login": true,
    "credenciales_backend": true,
    "url_licencia": "https://tu-servidor-licencias.com"
  }
}
```

### Paso 4: Construir Contenedores

```bash
# Descargar imágenes y construir contenedores
docker compose build

# Esto puede tomar 15-30 minutos la primera vez
```

### Paso 5: Iniciar el Sistema

```bash
# Iniciar todos los servicios en background
docker compose up -d

# Verificar que todos estén corriendo
docker compose ps

# Ver logs del portal
docker compose logs -f portal
```

### Paso 6: Verificar Instalación

```bash
# Verificar que el portal está corriendo
curl http://localhost:8080

# Deberías ver HTML del portal o una respuesta 200
```

---

## ⚙️ Configuración Detallada

### Archivo `config.json`

El archivo `config.json` es el corazón de la configuración. Aquí se detallan todos los parámetros:

#### Sección `portal`

```json
"portal": {
  "title": "Título mostrado en el navegador",
  "logo_url": "/static/images/logo.png",
  "theme": "light" | "dark",
  "idioma": "es" | "en"
}
```

#### Sección `clases`

Cada clase requiere:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `id` | Identificador único | `clase-001` |
| `nombre` | Nombre visible | `Matemáticas Financieras` |
| `profesor` | Nombre del profesor responsable | `Dr. Juan García` |
| `codigo` | Código de clase en la universidad | `MF-401-A` |
| `horarios` | Array de días y horas | Ver ejemplo abajo |
| `alumnos` | Array de alumnos registrados | Ver ejemplo abajo |
| `max_sesiones` | Máximo de contenedores para esta clase | `25` |
| `contenedor_prefix` | Prefijo para nombres de contenedores | `kasm-clase-001` |

**Ejemplo de Horarios:**

```json
"horarios": [
  {
    "dia": "lunes",
    "inicio": "09:00",
    "fin": "11:00"
  },
  {
    "dia": "miércoles",
    "inicio": "09:00",
    "fin": "11:00"
  }
]
```

Días válidos: `lunes`, `martes`, `miércoles`, `jueves`, `viernes`, `sábado`, `domingo`

**Ejemplo de Alumnos:**

```json
"alumnos": [
  {
    "id": "alumno_001",
    "nombre": "Carlos López",
    "matricula": "AL202401",
    "usuario": "clopez",
    "password": "GeneradoAutomaticamente123!"
  }
]
```

#### Sección `kasm`

Configuración de contenedores KasmVNC:

```json
"kasm": {
  "puerto_inicio": 6901,
  "imagen": "kasmweb/kasm-ubuntu:develop",
  "memoria_por_contenedor": "2.5G",
  "cpus_por_contenedor": 2,
  "timeout_sesion": 3600,  // segundos (1 hora)
  "timeout_inactividad": 1800  // segundos (30 minutos)
}
```

#### Sección `refinitiv`

```json
"refinitiv": {
  "auto_login": true,  // Login automático al iniciar Chrome
  "credenciales_backend": true,  // Credenciales gestionadas por backend
  "url_licencia": "https://tu-servidor-licencias.com"
}
```

### Modificar Configuración en Tiempo Real

Para cambiar la configuración sin reiniciar:

```bash
# 1. Editar config.json
nano config.json

# 2. Recargar la configuración en el portal
curl -X POST http://localhost:8080/api/reload-config \
  -H "Authorization: Bearer tu_token_admin"

# 3. Si es necesario, reiniciar contenedores específicos
docker compose restart portal
```

### Agregar una Nueva Clase

1. Edita `config.json`
2. Agrega un nuevo objeto en el array `clases`
3. Agrega los alumnos correspondientes
4. Agrega profesores en la sección `profesores`
5. Recarga la configuración:

```bash
curl -X POST http://localhost:8080/api/reload-config \
  -H "Authorization: Bearer token_admin"
```

---

## 👥 Uso del Sistema

### Para Alumnos

#### Acceso a Refinitiv Workspace

1. **Abrir el navegador** y dirigirse a:
   ```
   http://servidor:8080
   ```
   o
   ```
   https://streamapps.tuuniversidad.edu
   ```

2. **Iniciar sesión**:
   - Ingresa tu **usuario de clase**
   - Ingresa tu **contraseña**
   - Haz clic en "Acceder a Refinitiv"

3. **Esperar la creación de sesión** (30-60 segundos):
   - Se abrirá una nueva ventana con tu sesión privada
   - Verás el escritorio con Chrome abierto
   - Refinitiv Workspace estará precargado

4. **Usar Refinitiv**:
   - La sesión es completamente privada
   - Puedes navegar, crear portafolios, ejecutar análisis
   - Todas las tus acciones están aisladas

5. **Cerrar sesión**:
   - Haz clic en "Cerrar Sesión" en el portal
   - Volverás automáticamente al login
   - Tu contenedor se eliminará después del tiempo de inactividad

#### Problemas Comunes (Alumnos)

| Problema | Solución |
|----------|----------|
| "Usuario o contraseña incorrectos" | Verifica que ingresaste correctamente. Contacta a tu profesor. |
| La sesión es muy lenta | Cierra otras aplicaciones. Intenta de nuevo en otro momento. |
| Chrome no carga | Espera 60 segundos. Refresca la página (F5). |
| Se cortó la conexión | Inicia sesión de nuevo. Tu sesión anterior se cerrará en 30 min. |

### Para Profesores

#### Acceso al Dashboard

1. **Iniciar sesión con credenciales de profesor**:
   - Usuario: `jgarcia` (ejemplo)
   - Contraseña: Tu contraseña segura

2. **Ver Dashboard de Supervisión**:
   - Lista de alumnos conectados en tu clase
   - Duración de cada sesión
   - Recursos utilizados por estudiante
   - Botón para finalizar sesiones si es necesario

3. **Monitorear Actividad**:
   - Visualizar quién está conectado ahora
   - Historial de accesos (últimos 7 días)
   - Descargar reportes de actividad

#### Funciones Disponibles para Profesores

- ✅ Ver lista de alumnos de tu clase
- ✅ Monitorear sesiones activas
- ✅ Finalizar sesiones problemáticas
- ✅ Descargar reportes de actividad
- ✅ Ver estadísticas de uso
- ✅ Cambiar contraseña

---

## 🔐 Credenciales por Defecto

Las siguientes son credenciales de ejemplo iniciales. **Cámbialas inmediatamente en producción**.

### Alumnos

| Clase | Matrícula | Usuario | Contraseña | Email |
|-------|-----------|---------|-----------|-------|
| Matemáticas Financieras A | AL202401 | clopez | GeneradoAutomaticamente123! | carlos.lopez@universidadanáhuac.edu |
| Matemáticas Financieras A | AL202402 | mgonzalez | GeneradoAutomaticamente456! | maria.gonzalez@universidadanáhuac.edu |
| Análisis Técnico B | AL202403 | psanchez | GeneradoAutomaticamente789! | pedro.sanchez@universidadanáhuac.edu |

### Profesores

| Nombre | Usuario | Contraseña Inicial | Email |
|--------|---------|-------------------|-------|
| Dr. Juan García | jgarcia | PasswordSeguroProfesor001! | juan.garcia@universidadanáhuac.edu |
| Dra. Rosa Martínez | rmartinez | PasswordSeguroProfesor002! | rosa.martinez@universidadanáhuac.edu |

### Administrador

| Usuario | Contraseña Inicial |
|---------|-------------------|
| admin | PasswordSeguroAdmin123! |

⚠️ **IMPORTANTE**: Todos estos deben cambiar en tu `config.json` ANTES de desplegar en producción.

---

## 🔌 Puertos

### Puertos del Sistema

| Puerto | Servicio | Descripción |
|--------|---------|-------------|
| **8080** | Portal Web | Interfaz de login y gestión |
| **6901** | KasmVNC Clase 1 | Contenedor 1 de estudiantes |
| **6902** | KasmVNC Clase 2 | Contenedor 2 de estudiantes |
| **6903-6925** | KasmVNC Clases 3-25 | Contenedores 3-25 de estudiantes |
| **3306** (opt.) | Base de Datos | MariaDB (si está habilitado) |
| **5432** (opt.) | PostgreSQL | Base de datos alternativa |

### Verificar Puertos Disponibles

```bash
# En Linux/macOS
sudo lsof -i -P -n | grep LISTEN

# En macOS usando netstat
netstat -tuln | grep LISTEN

# Ver solo puerto específico
lsof -i :8080
```

### Cambiar Puertos

Para cambiar los puertos por defecto, edita `docker-compose.yml`:

```yaml
services:
  portal:
    ports:
      - "9090:8080"  # Cambiar 8080 a 9090 externamente

  kasm-class-001:
    ports:
      - "7001:6901"  # Cambiar puerto de acceso
```

Luego reinicia:

```bash
docker compose down
docker compose up -d
```

---

## 🔧 Troubleshooting

### Problemas Comunes y Soluciones

#### 1. Chrome No Arranca en el Contenedor

**Síntoma**: Haces login pero Chrome no se abre en la sesión.

**Soluciones**:

```bash
# Ver logs del contenedor específico
docker logs kasm-clase-001-alumno001

# Reiniciar el contenedor
docker restart kasm-clase-001-alumno001

# Verificar recursos disponibles
docker stats

# Si la RAM es insuficiente
# Reduce memoria_por_contenedor en config.json de 2.5G a 2G
```

#### 2. Errores de DNS

**Síntoma**: El navegador dice "No se puede resolver el servidor"

**Soluciones**:

```bash
# Verificar DNS dentro del contenedor
docker exec kasm-clase-001-alumno001 cat /etc/resolv.conf

# Agregar DNS personalizado en docker-compose.yml
kasm-session:
  dns:
    - 8.8.8.8
    - 8.8.4.4

# Reiniciar Docker
docker compose down
docker compose up -d
```

#### 3. Certificado SSL No Válido

**Síntoma**: "HTTPS - Certificado no es seguro"

**Soluciones**:

```bash
# Generar certificado auto-firmado
mkdir -p ./certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./certs/key.pem \
  -out ./certs/cert.pem

# Editar docker-compose.yml para usar HTTPS
environment:
  - USE_HTTPS=true
  - CERT_PATH=/certs/cert.pem
  - KEY_PATH=/certs/key.pem

# Reiniciar
docker compose down
docker compose up -d
```

#### 4. Contenedores No Inician - Error de Memoria

**Síntoma**: `docker compose up` falla con "OOMKilled" o "Out of memory"

**Soluciones**:

```bash
# Verificar RAM disponible
free -h

# Reducir contenedores simultáneos en config.json
"max_sesiones": 10  # en lugar de 25

# O reducir memoria por contenedor
"memoria_por_contenedor": "1.5G"  # en lugar de 2.5G

# Recompilar y reiniciar
docker compose down
docker compose build --no-cache
docker compose up -d
```

#### 5. Portal No Responde (Puerto 8080)

**Síntoma**: `curl http://localhost:8080` no responde

**Soluciones**:

```bash
# Ver status del contenedor portal
docker compose ps

# Ver logs del portal
docker compose logs -f portal

# Verificar que puerto no esté en uso
lsof -i :8080

# Si está en uso, cambiar puerto en docker-compose.yml
# Luego:
docker compose down
docker compose up -d
```

#### 6. Los Alumnos No Pueden Iniciar Sesión

**Síntoma**: "Usuario o contraseña incorrectos" para alumnos válidos

**Soluciones**:

```bash
# Verificar que config.json sea válido JSON
json -f config.json

# Ver logs del portal para errores de autenticación
docker compose logs -f portal | grep -i auth

# Verificar que el usuario existe en config.json
grep "usuario" config.json

# Recargar configuración
curl -X POST http://localhost:8080/api/reload-config \
  -H "Authorization: Bearer token_admin"
```

#### 7. Las Sesiones Se Cierran Muy Rápido

**Síntoma**: Los alumnos se desconectan después de 5-10 minutos

**Soluciones**:

```bash
# Aumentar timeout de inactividad en config.json
"timeout_inactividad": 3600  # 1 hora en lugar de 30 min
"timeout_sesion": 7200  # 2 horas en lugar de 1 hora

# Recargar configuración
curl -X POST http://localhost:8080/api/reload-config

# Ver logs de Kasm para ver por qué se cierran
docker logs kasm-clase-001-alumno001 | tail -50
```

#### 8. Refinitiv No Carga en Chrome

**Síntoma**: Página en blanco o error 403 al acceder a Refinitiv

**Soluciones**:

```bash
# Verificar que las credenciales en .env son correctas
cat .env | grep REFINITIV

# Probar credenciales manualmente
curl -u "$REFINITIV_USERNAME:$REFINITIV_PASSWORD" \
  https://eikon.refinitiv.com

# Verificar que Chrome puede acceder a internet
docker exec kasm-clase-001-alumno001 \
  curl https://www.google.com

# Revisar la configuración de proxy si aplica
```

---

## 🛠️ Mantenimiento

### Reiniciar el Sistema

#### Reinicio Suave (Sin Perder Sesiones Activas)

```bash
# Recargar solo el portal
docker compose restart portal

# Verificar que reinició correctamente
docker compose ps
curl http://localhost:8080
```

#### Reinicio Completo (Se Pierden Sesiones)

```bash
# Detener todos los servicios
docker compose down

# Esperar 5 segundos
sleep 5

# Reiniciar todo
docker compose up -d

# Verificar status
docker compose ps
```

### Actualizar el Sistema

```bash
# 1. Detener servicios
docker compose down

# 2. Descargar últimas imágenes
docker compose pull

# 3. Recompilar si hay cambios locales
docker compose build

# 4. Iniciar nuevamente
docker compose up -d

# 5. Verificar
docker compose ps
docker compose logs portal
```

### Limpiar Sesiones Antiguas

#### Limpiar Manualmente

```bash
# Ver todos los contenedores
docker ps -a

# Eliminar contenedores detenidos
docker container prune

# Eliminar imágenes no usadas
docker image prune

# Eliminar volúmenes no usados
docker volume prune
```

#### Script Automático de Limpieza

Crea `cleanup.sh`:

```bash
#!/bin/bash

echo "Limpiando sesiones antigas..."

# Eliminar contenedores que hayan estado detenidos más de 1 hora
docker ps -a --filter "status=exited" \
  --filter "before=1h" -q | xargs -r docker rm

# Limpiar volúmenes no usados
docker volume prune -f

# Limpiar imágenes dangling
docker image prune -f

echo "Limpieza completada"
```

Ejecución:

```bash
chmod +x cleanup.sh
./cleanup.sh
```

O programar con cron:

```bash
# Ejecutar limpieza cada día a las 2 AM
0 2 * * * /ruta/al/proyecto/cleanup.sh >> /var/log/uam-streamapps-cleanup.log 2>&1
```

### Monitorear Recursos

#### Ver Uso de Recursos en Tiempo Real

```bash
# Monitorar todos los contenedores
docker stats

# Monitorar específicamente portal
docker stats portal

# Guardar estadísticas en archivo
docker stats --no-stream > stats.txt
```

#### Configurar Alertas

```bash
# Ver si hay contenedores usando más del 80% de RAM
docker stats --no-stream | awk 'NR>1 {
  gsub(/%/, "", $7)
  if ($7 > 80) print $2, "usando", $7, "% de RAM"
}'
```

### Backups

#### Respaldar Configuración

```bash
# Crear carpeta de backups
mkdir -p ./backups

# Respaldar archivos críticos
tar -czf ./backups/config-$(date +%Y%m%d-%H%M%S).tar.gz \
  config.json .env docker-compose.yml

# Listar backups
ls -lh ./backups/
```

#### Respaldar Volúmenes

```bash
# Ver volúmenes
docker volume ls

# Respaldar un volumen específico
docker run --rm -v uam-streamapps_data:/data \
  -v ./backups:/backup \
  alpine tar czf /backup/volume-data-$(date +%Y%m%d).tar.gz \
  -C /data .

# Restaurar desde backup
docker run --rm -v uam-streamapps_data:/data \
  -v ./backups:/backup \
  alpine tar xzf /backup/volume-data-20240115.tar.gz \
  -C /data
```

### Rotación de Logs

Docker mantiene logs automáticamente, pero puedes configurar límites:

Crea `daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

En macOS (Docker Desktop):
- Preferencias → Docker Engine → Agregar contenido anterior

En Linux:
```bash
sudo nano /etc/docker/daemon.json
# Agregar contenido
sudo systemctl restart docker
```

### Actualizar Contraseñas

#### Cambiar Contraseña de Alumno

1. Editar `config.json`
2. Encontrar el alumno en la sección correspondiente
3. Cambiar el campo `password`
4. Recargar configuración:

```bash
curl -X POST http://localhost:8080/api/reload-config \
  -H "Authorization: Bearer token_admin"
```

#### Cambiar Contraseña de Profesor

```bash
# A través de la API (si está implementada)
curl -X POST http://localhost:8080/api/cambiar-password \
  -H "Authorization: Bearer token_profesor" \
  -H "Content-Type: application/json" \
  -d '{"password_nuevo": "NuevaContraseñaSegura123!"}'
```

O editar directamente en `config.json` y recargar.

### Ver Registros de Actividad

```bash
# Logs del portal (últimas 100 líneas)
docker compose logs --tail=100 portal

# Logs de un contenedor específico
docker compose logs kasm-clase-001-alumno001

# Logs en tiempo real
docker compose logs -f

# Guardar logs en archivo
docker compose logs > logs-$(date +%Y%m%d-%H%M%S).txt
```

---

## 📊 Estadísticas de Desempeño

Una vez en producción, monitorea estas métricas:

### Recursos del Sistema

```bash
# CPU y Memoria en tiempo real
docker stats --no-stream --format \
  "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Almacenamiento
docker system df

# Red
docker exec portal netstat -tuln | grep LISTEN
```

### Sesiones de Usuarios

```bash
# Conectados ahora
curl http://localhost:8080/api/sesiones-activas

# Historial de sesiones
curl http://localhost:8080/api/historial-sesiones?limit=50
```

---

## ⚠️ Consideraciones de Seguridad

### En Producción

1. **Cambiar todas las contraseñas por defecto** ✅
2. **Usar HTTPS** con certificado válido ✅
3. **Configurar firewall** para restricciones de acceso ✅
4. **Usar VPN** o red privada si es posible ✅
5. **Habilitar autenticación 2FA** si es posible ✅
6. **Hacer backups regulares** ✅
7. **Monitorear logs regularmente** ✅
8. **Usar contraseñas fuertes** (mínimo 12 caracteres) ✅

### Generador de Contraseñas Seguras

```bash
# Generar contraseña aleatoria
openssl rand -base64 12

# Ejemplos:
# L9kX+2pMqR8vN3wY
# 7sH4gJ2xB6cK9pL1
# Fq5RvTd8jW2mN6xK
```

---

## 📞 Soporte

Para reportar problemas o sugerencias:

- **Email de Soporte**: soporte@universidadanáhuac.edu
- **Equipo IT**: it-services@universidadanáhuac.edu
- **Repositorio GitHub**: https://github.com/tuorganizacion/uam-streamapps/issues

### Información para Reportar Problemas

Cuando reportes un problema, incluye:

```
1. Descripción clara del problema
2. Pasos para reproducirlo
3. Captura de pantalla (si aplica)
4. Nombre de usuario y clase
5. Hora exacta del incidente
6. Salida de: docker compose ps
7. Últimas líneas de: docker compose logs --tail=50
```

---

## 📝 Licencia

Este proyecto es propiedad de la **Universidad Anáhuac Mayab**.

Uso interno únicamente. No autorizado para distribución o uso externo sin consentimiento explícito.

---

## 🎓 Créditos

- **Desarrollado por**: Equipo IT - Universidad Anáhuac Mayab
- **Basado en**: Docker, KasmVNC, Google Chrome
- **Refinitiv**: Plataforma financiera profesional

---

## 📋 Checklist de Implementación

Use esta lista para seguimiento:

- [ ] Hardware validado (RAM, CPU, Disco)
- [ ] Docker y Docker Compose instalados
- [ ] Proyecto clonado/copiado en `/data/uam-streamapps`
- [ ] `.env` configurado con valores correctos
- [ ] `config.json` completado con clases y alumnos
- [ ] `docker compose build` completado exitosamente
- [ ] `docker compose up -d` iniciado
- [ ] Portal accesible en http://localhost:8080
- [ ] Login de alumno probado
- [ ] Login de profesor probado
- [ ] Dashboard de profesor funcional
- [ ] Refinitiv abierto correctamente en contenedor
- [ ] Timeout de sesiones configurado
- [ ] Backups automáticos configurados
- [ ] Logs monitoreados
- [ ] Contraseñas por defecto cambiadas
- [ ] HTTPS configurado (si aplica)
- [ ] Documentación completada
- [ ] Equipo capacitado

---

**Última actualización**: Septiembre 2026

**Versión**: 1.0.0

**Estado**: Producción
