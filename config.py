# ---------------------------------------------------
# CONFIGURACION DEL TALLER
# ---------------------------------------------------
# Este archivo primero busca cada valor como VARIABLE DE ENTORNO
# (las que cargas en Render -> Environment). Si no la encuentra
# (por ejemplo cuando corres algo en tu compu), usa el valor de
# respaldo que esta al lado del "os.environ.get(...)".
#
# Asi podes subir este archivo a GitHub sin miedo: los datos
# sensibles reales viven solo en Render, nunca en el repositorio.

import os

# Host/puerto en los que corre Flask (esto lo maneja el hosting, no lo toques).
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

# URL PUBLICA del servidor una vez desplegado (Render, Railway, PythonAnywhere, etc).
# La app de escritorio (admin_app.py) SIEMPRE corre en tu compu, asi que a ESTA
# la tenes que escribir vos aca abajo (no hace falta cargarla en Render).
# Ejemplo: "https://mi-taller.onrender.com"
PUBLIC_URL = "https://ww-57bu.onrender.com"

# Clave para que solo vos puedas administrar el inventario desde admin_app.py.
# En Render: Environment Variable ADMIN_KEY = tu-clave-secreta
# Aca en tu compu: pega la MISMA clave en el respaldo de abajo (despues de la coma).
ADMIN_KEY = os.environ.get("ADMIN_KEY", "pega-aca-tu-clave-secreta")

# --- WhatsApp (CallMeBot) ---
# En Render cargas: WHATSAPP_ENABLED=True, WHATSAPP_PHONE=..., WHATSAPP_APIKEY=...
# (estas tres solo las necesita el SERVIDOR en la nube, no tu compu)
WHATSAPP_ENABLED = os.environ.get("WHATSAPP_ENABLED", "False") == "True"
WHATSAPP_PHONE = os.environ.get("WHATSAPP_PHONE", "")
WHATSAPP_APIKEY = os.environ.get("WHATSAPP_APIKEY", "")
