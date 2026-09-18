#!/usr/bin/env bash
# =============================================================================
# Wrapper personalizado para Google Chrome en Kasm - UAM StreamApps
# Gestiona persistencia de datos y lanzamiento seguro del navegador
# =============================================================================

# Limpiar Singleton locks si Chrome no está corriendo
if ! pgrep chrome > /dev/null; then
  rm -f $HOME/.config/google-chrome/Singleton*
  rm -f /opt/chrome-data/Singleton*
fi

# Determinar directorio de datos de Chrome
CHROME_DATA="/opt/chrome-data"
if [ -d "$CHROME_DATA" ]; then
    DATA_DIR_FLAG="--user-data-dir=$CHROME_DATA"
    # Limpiar estado de crash en directorio persistente
    if [ -f "$CHROME_DATA/Default/Preferences" ]; then
        sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' "$CHROME_DATA/Default/Preferences"
        sed -i 's/"exit_type":"Crashed"/"exit_type":"None"/' "$CHROME_DATA/Default/Preferences"
    fi
else
    DATA_DIR_FLAG="--user-data-dir"
    # Limpiar estado de crash en directorio por defecto
    if [ -f ~/.config/google-chrome/Default/Preferences ]; then
        sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/google-chrome/Default/Preferences
        sed -i 's/"exit_type":"Crashed"/"exit_type":"None"/' ~/.config/google-chrome/Default/Preferences
    fi
fi

# Lanzar Chrome con flags optimizados para contenedor
if [ -f /opt/VirtualGL/bin/vglrun ] && [ ! -z "${KASM_EGL_CARD}" ] && [ ! -z "${KASM_RENDERD}" ] && [ -O "${KASM_RENDERD}" ] && [ -O "${KASM_EGL_CARD}" ] ; then
    echo "Starting Chrome with GPU Acceleration on EGL device ${KASM_EGL_CARD}"
    vglrun -d "${KASM_EGL_CARD}" /opt/google/chrome/google-chrome --password-store=basic --no-sandbox --ignore-gpu-blocklist $DATA_DIR_FLAG --no-first-run --simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT' "$@"
else
    echo "Starting Chrome"
    /opt/google/chrome/google-chrome --password-store=basic --no-sandbox --ignore-gpu-blocklist $DATA_DIR_FLAG --no-first-run --simulate-outdated-no-au='Tue, 31 Dec 2099 23:59:59 GMT' "$@"
fi
