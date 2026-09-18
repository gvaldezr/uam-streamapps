"""
UAM StreamApps — Portal de Acceso
Aplicación Flask que gestiona el acceso a contenedores Kasm con Refinitiv Workspace.
"""

import json
import os
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "uam-streamapps-secret-key-change-me")

CONFIG_PATH = os.environ.get("CONFIG_PATH", "/app/config.json")
TIMEOUT_HORAS = float(os.environ.get("TIMEOUT_HORAS", "3"))

# ---------------------------------------------------------------------------
# Estado en memoria: tracking de contenedores
# ---------------------------------------------------------------------------

containers: list[dict] = []
containers_lock = threading.Lock()


def init_containers(cantidad: int, puerto_base: int) -> None:
    """Inicializa la lista de contenedores."""
    global containers
    containers = []
    for i in range(cantidad):
        containers.append(
            {
                "id": i + 1,
                "puerto": puerto_base + i,
                "estado": "libre",
                "clase": None,
                "usuario": None,
                "hora_conexion": None,
                "hora_conexion_ts": None,
            }
        )


# ---------------------------------------------------------------------------
# Carga de configuración
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Lee config.json del path configurado."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        app.logger.error("No se encontró config.json en %s", CONFIG_PATH)
        return {}
    except json.JSONDecodeError as exc:
        app.logger.error("Error al parsear config.json: %s", exc)
        return {}


config = load_config()

# Inicializar contenedores según config
_cont_cfg = config.get("contenedores", {})
init_containers(
    cantidad=_cont_cfg.get("cantidad", 25),
    puerto_base=_cont_cfg.get("puerto_base", 6901),
)


# ---------------------------------------------------------------------------
# Utilidades de zona horaria (stdlib puro Python 3.9+)
# ---------------------------------------------------------------------------

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore

TIMEZONE = ZoneInfo("America/Mexico_City")

DIAS_MAP = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}


def ahora_cdmx() -> datetime:
    """Retorna datetime actual en zona horaria America/Mexico_City."""
    return datetime.now(tz=TIMEZONE)


def es_horario_clase(horario: dict) -> bool:
    """Verifica si el momento actual cae dentro del horario de la clase."""
    now = ahora_cdmx()
    dia_actual = DIAS_MAP.get(now.weekday(), "")

    if dia_actual not in horario.get("dias_semana", []):
        return False

    hora_inicio = datetime.strptime(horario["hora_inicio"], "%H:%M").time()
    hora_fin = datetime.strptime(horario["hora_fin"], "%H:%M").time()
    hora_actual = now.time()

    return hora_inicio <= hora_actual <= hora_fin


# ---------------------------------------------------------------------------
# Autenticación
# ---------------------------------------------------------------------------

def autenticar(usuario: str, clave: str) -> dict | None:
    """
    Verifica credenciales contra config.json.
    Retorna dict con info del usuario o None si inválidas.
    """
    clases = config.get("clases", {})
    for clase_id, clase_data in clases.items():
        creds = clase_data.get("credenciales", {})

        # Verificar alumno
        alumno_cred = creds.get("alumno", {})
        if alumno_cred.get("usuario") == usuario and alumno_cred.get("password") == clave:
            return {"usuario": usuario, "rol": "alumno", "clase": clase_id}

        # Verificar profesor
        prof_cred = creds.get("profesor", {})
        if prof_cred.get("usuario") == usuario and prof_cred.get("password") == clave:
            return {"usuario": usuario, "rol": "profesor", "clase": clase_id}

    return None


def login_required(f):
    """Decorador que requiere sesión activa."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------------
# Gestión de contenedores
# ---------------------------------------------------------------------------

def asignar_contenedor(clase: str, usuario: str) -> dict | None:
    """Asigna el primer contenedor libre."""
    with containers_lock:
        for c in containers:
            if c["estado"] == "libre":
                now = ahora_cdmx()
                c["estado"] = "ocupado"
                c["clase"] = clase
                c["usuario"] = usuario
                c["hora_conexion"] = now.strftime("%Y-%m-%d %H:%M:%S")
                c["hora_conexion_ts"] = now.timestamp()
                return c.copy()
    return None


def liberar_contenedor(container_id: int) -> bool:
    """Libera un contenedor por su ID."""
    with containers_lock:
        for c in containers:
            if c["id"] == container_id:
                c["estado"] = "libre"
                c["clase"] = None
                c["usuario"] = None
                c["hora_conexion"] = None
                c["hora_conexion_ts"] = None
                return True
    return False


def liberar_contenedor_por_usuario(usuario: str) -> bool:
    """Libera todos los contenedores asignados a un usuario."""
    found = False
    with containers_lock:
        for c in containers:
            if c["usuario"] == usuario:
                c["estado"] = "libre"
                c["clase"] = None
                c["usuario"] = None
                c["hora_conexion"] = None
                c["hora_conexion_ts"] = None
                found = True
    return found


def obtener_estado_contenedores() -> list[dict]:
    """Retorna copia del estado de todos los contenedores."""
    with containers_lock:
        return [c.copy() for c in containers]


def auto_liberar_timeout():
    """Libera contenedores que exceden el timeout configurado."""
    now_ts = ahora_cdmx().timestamp()
    timeout_seg = TIMEOUT_HORAS * 3600
    with containers_lock:
        for c in containers:
            if c["estado"] == "ocupado" and c["hora_conexion_ts"]:
                if now_ts - c["hora_conexion_ts"] > timeout_seg:
                    app.logger.info(
                        "Auto-liberando contenedor %d (timeout %s hrs)",
                        c["id"],
                        TIMEOUT_HORAS,
                    )
                    c["estado"] = "libre"
                    c["clase"] = None
                    c["usuario"] = None
                    c["hora_conexion"] = None
                    c["hora_conexion_ts"] = None


# ---------------------------------------------------------------------------
# Hilo de limpieza (auto-liberar por timeout)
# ---------------------------------------------------------------------------

def cleanup_thread():
    """Ejecuta limpieza periódica cada 60 segundos."""
    while True:
        time.sleep(60)
        try:
            auto_liberar_timeout()
        except Exception as exc:
            app.logger.error("Error en cleanup_thread: %s", exc)


_cleanup = threading.Thread(target=cleanup_thread, daemon=True)
_cleanup.start()


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "usuario" in session:
        if session.get("rol") == "profesor":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("conectar"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "").strip()

        user_info = autenticar(usuario, clave)
        if not user_info:
            flash("Usuario o contraseña incorrectos.", "error")
            return render_template("login.html")

        # Guardar sesión
        session["usuario"] = user_info["usuario"]
        session["rol"] = user_info["rol"]
        session["clase"] = user_info["clase"]

        if user_info["rol"] == "profesor":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("conectar"))

    return render_template("login.html")


@app.route("/conectar")
@login_required
def conectar():
    """Lógica de conexión para alumnos."""
    clase_id = session.get("clase")
    usuario = session.get("usuario")
    rol = session.get("rol")
    clase_data = config.get("clases", {}).get(clase_id, {})
    horario = clase_data.get("horario", {})
    nombre_clase = clase_data.get("nombre", f"Clase {clase_id}")

    # Los profesores se redirigen al dashboard
    if rol == "profesor":
        return redirect(url_for("dashboard"))

    # Verificar horario para alumnos
    if not es_horario_clase(horario):
        hora_inicio = horario.get("hora_inicio", "??")
        hora_fin = horario.get("hora_fin", "??")
        dias = ", ".join(horario.get("dias_semana", []))
        return render_template(
            "login.html",
            fuera_de_horario=True,
            nombre_clase=nombre_clase,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            dias=dias,
        )

    # Identificador único por sesión de navegador (no por usuario de clase)
    # Esto permite que múltiples alumnos con el mismo login de clase
    # obtengan contenedores diferentes
    session_id = session.sid if hasattr(session, 'sid') else session.get("_id", id(session))
    if "session_uid" not in session:
        import uuid
        session["session_uid"] = str(uuid.uuid4())
    session_uid = session["session_uid"]

    # ¿Ya tiene un contenedor asignado esta sesión?
    container_asignado = None
    with containers_lock:
        for c in containers:
            if c["usuario"] == session_uid and c["estado"] == "ocupado":
                container_asignado = c.copy()
                break

    if not container_asignado:
        container_asignado = asignar_contenedor(clase_id, session_uid)

    if not container_asignado:
        flash("No hay contenedores disponibles en este momento. Intenta de nuevo en unos minutos.", "error")
        return render_template("login.html")

    # Construir URL del contenedor Kasm
    host = request.host.split(":")[0]
    puerto = container_asignado["puerto"]
    vnc_clave = config.get("contenedores", {}).get("vnc", {}).get("password", "")
    # Redirigir a través de Nginx reverse proxy (inyecta BasicAuth automáticamente)
    # Redirigir a través de Nginx (puerto 8900 + id del contenedor)
    proxy_port = 8900 + container_asignado["id"]
    kasm_url = f"https://{host}:{proxy_port}"

    session["container_id"] = container_asignado["id"]
    session["container_puerto"] = puerto

    return render_template(
        "session.html",
        kasm_url=kasm_url,
        kasm_host=host,
        kasm_port=puerto,
        vnc_clave=vnc_clave,
        container_id=container_asignado["id"],
        nombre_clase=nombre_clase,
    )


@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard del profesor."""
    if session.get("rol") != "profesor":
        return redirect(url_for("conectar"))

    estado = obtener_estado_contenedores()
    libres = sum(1 for c in estado if c["estado"] == "libre")
    ocupados = sum(1 for c in estado if c["estado"] == "ocupado")
    host = request.host.split(":")[0]

    # Info de clases para mostrar horarios
    clases = config.get("clases", {})
    clases_info = {}
    for cid, cdata in clases.items():
        clases_info[cid] = {
            "nombre": cdata.get("nombre", f"Clase {cid}"),
            "hora_inicio": cdata.get("horario", {}).get("hora_inicio", ""),
            "hora_fin": cdata.get("horario", {}).get("hora_fin", ""),
            "dias": ", ".join(cdata.get("horario", {}).get("dias_semana", [])),
        }

    now = ahora_cdmx().strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        "dashboard.html",
        contenedores=estado,
        libres=libres,
        ocupados=ocupados,
        total=len(estado),
        host=host,
        clases_info=clases_info,
        hora_actual=now,
        clase_profesor=session.get("clase"),
    )


@app.route("/profesor/entrar/<int:container_id>")
@login_required
def profesor_entrar(container_id: int):
    """Permite al profesor entrar a cualquier contenedor."""
    if session.get("rol") != "profesor":
        return redirect(url_for("conectar"))

    host = request.host.split(":")[0]
    vnc_clave = config.get("contenedores", {}).get("vnc", {}).get("password", "")

    target = None
    with containers_lock:
        for c in containers:
            if c["id"] == container_id:
                target = c.copy()
                break

    if not target:
        flash("Contenedor no encontrado.", "error")
        return redirect(url_for("dashboard"))

    vnc_clave = config.get("contenedores", {}).get("vnc", {}).get("password", "")
    proxy_port = 8900 + target["id"]
    kasm_url = f"https://{host}:{proxy_port}"
    nombre_clase = config.get("clases", {}).get(session.get("clase", ""), {}).get("nombre", "Profesor")

    return render_template(
        "session.html",
        kasm_url=kasm_url,
        kasm_host=host,
        kasm_port=target["puerto"],
        vnc_clave=vnc_clave,
        container_id=target["id"],
        nombre_clase=nombre_clase,
        es_profesor=True,
    )


@app.route("/kasm-viewer/<int:container_id>")
@login_required
def kasm_viewer(container_id: int):
    """
    Relay page (mismo origen que el portal) que embebe la sesión Kasm en un
    iframe a pantalla completa.

    ¿Por qué existe?
    ----------------
    La pestaña de Kasm corre en https://host:8901 (origen distinto al portal
    http://host:8080). Una ventana no puede cerrar de forma fiable a otra de
    distinto origen, y la referencia `window.open()` se pierde cuando la página
    que la abrió recarga (p. ej. tras el POST de logout).

    Al abrir en su lugar esta página —servida por el propio portal— la pestaña
    resultante es *mismo origen* que session.html. Eso permite usar un
    BroadcastChannel para que, al hacer logout, esta página cierre su PROPIA
    ventana con window.close() (operación siempre permitida sobre ventanas
    abiertas por script del mismo origen).
    """
    host = request.host.split(":")[0]
    proxy_port = 8900 + container_id
    kasm_url = f"https://{host}:{proxy_port}"
    return render_template(
        "kasm_viewer.html",
        kasm_url=kasm_url,
        container_id=container_id,
    )


@app.route("/liberar/<int:container_id>", methods=["POST"])
@login_required
def liberar(container_id: int):
    """Libera un contenedor (profesor o el propio alumno)."""
    rol = session.get("rol")
    session_uid = session.get("session_uid")

    if rol == "profesor":
        liberar_contenedor(container_id)
    else:
        with containers_lock:
            for c in containers:
                if c["id"] == container_id and c["usuario"] == session_uid:
                    c["estado"] = "libre"
                    c["clase"] = None
                    c["usuario"] = None
                    c["hora_conexion"] = None
                    c["hora_conexion_ts"] = None
                    break

    if rol == "profesor":
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """Cierra sesión y libera contenedor del alumno."""
    usuario = session.get("usuario")
    rol = session.get("rol")
    session_uid = session.get("session_uid")

    if session_uid and rol == "alumno":
        liberar_contenedor_por_usuario(session_uid)

    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# API de monitoreo
# ---------------------------------------------------------------------------

@app.route("/api/status")
def api_status():
    """Endpoint JSON para monitoreo externo."""
    estado = obtener_estado_contenedores()
    libres = sum(1 for c in estado if c["estado"] == "libre")
    ocupados = sum(1 for c in estado if c["estado"] == "ocupado")
    now = ahora_cdmx()

    clases_status = {}
    for cid, cdata in config.get("clases", {}).items():
        horario = cdata.get("horario", {})
        clases_status[cid] = {
            "nombre": cdata.get("nombre", ""),
            "hora_inicio": horario.get("hora_inicio", ""),
            "hora_fin": horario.get("hora_fin", ""),
            "activa": es_horario_clase(horario),
        }

    return jsonify(
        {
            "timestamp": now.isoformat(),
            "contenedores": {
                "total": len(estado),
                "libres": libres,
                "ocupados": ocupados,
                "detalle": estado,
            },
            "clases": clases_status,
            "timeout_horas": TIMEOUT_HORAS,
        }
    )


@app.route("/api/status/resumen")
def api_status_resumen():
    """Resumen ligero para el auto-refresh del dashboard."""
    estado = obtener_estado_contenedores()
    libres = sum(1 for c in estado if c["estado"] == "libre")
    ocupados = sum(1 for c in estado if c["estado"] == "ocupado")
    now = ahora_cdmx().strftime("%Y-%m-%d %H:%M:%S")

    return jsonify(
        {
            "hora_actual": now,
            "libres": libres,
            "ocupados": ocupados,
            "total": len(estado),
            "contenedores": estado,
        }
    )


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
