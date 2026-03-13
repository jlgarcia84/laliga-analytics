"""
auth.py — Módulo de autenticación y gestión de sesión
Tarea 8 - Master Data Science / LaLiga Analytics
"""

import hashlib
import streamlit as st

# ---------------------------------------------------------------------------
# Base de usuarios (en producción esto vendría de una BD o fichero seguro)
# ---------------------------------------------------------------------------
# Las contraseñas se almacenan como hash SHA-256 para no guardarlas en claro.
# Para generar el hash de una contraseña:
#   import hashlib; hashlib.sha256("mi_pass".encode()).hexdigest()
# ---------------------------------------------------------------------------

USERS: dict[str, dict] = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "nombre": "Administrador",
        "rol": "admin",
        "equipo": None,
    },
    "analista": {
        "password_hash": hashlib.sha256("laliga2024".encode()).hexdigest(),
        "nombre": "Analista LaLiga",
        "rol": "analista",
        "equipo": None,
    },
    "villarreal": {
        "password_hash": hashlib.sha256("ycf2024".encode()).hexdigest(),
        "nombre": "Villarreal CF",
        "rol": "club",
        "equipo": "Villarreal CF",
    },
}


# ---------------------------------------------------------------------------
# Funciones de autenticación
# ---------------------------------------------------------------------------

def _hash_password(password: str) -> str:
    """Devuelve el hash SHA-256 de la contraseña recibida."""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, password: str) -> bool:
    """
    Valida las credenciales del usuario.

    Parámetros
    ----------
    username : str  — nombre de usuario introducido
    password : str  — contraseña en texto plano introducida

    Retorna
    -------
    True si las credenciales son correctas, False en caso contrario.
    """
    user = USERS.get(username.strip().lower())
    if user is None:
        return False
    return user["password_hash"] == _hash_password(password)


def get_user_info(username: str) -> dict | None:
    """Devuelve el diccionario con la información del usuario (sin hash)."""
    user = USERS.get(username.strip().lower())
    if user is None:
        return None
    return {k: v for k, v in user.items() if k != "password_hash"}


# ---------------------------------------------------------------------------
# Gestión de sesión con st.session_state
# ---------------------------------------------------------------------------

def init_session() -> None:
    """
    Inicializa las claves de sesión necesarias si todavía no existen.
    Debe llamarse al inicio de cada página de la aplicación.
    """
    defaults = {
        "logged_in": False,
        "username": None,
        "user_info": None,
        "login_attempts": 0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def login(username: str, password: str) -> bool:
    """
    Intenta iniciar sesión. Actualiza st.session_state si tiene éxito.

    Retorna True si el login fue correcto, False si falló.
    """
    if authenticate(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username.strip().lower()
        st.session_state.user_info = get_user_info(username)
        st.session_state.login_attempts = 0
        return True
    else:
        st.session_state.login_attempts += 1
        return False


def logout() -> None:
    """Cierra la sesión y limpia el estado."""
    for key in ["logged_in", "username", "user_info"]:
        st.session_state[key] = None if key != "logged_in" else False
    st.session_state.login_attempts = 0


def is_logged_in() -> bool:
    """Comprueba si hay una sesión activa."""
    return st.session_state.get("logged_in", False)


def require_login() -> bool:
    """
    Protege una página: si el usuario no está autenticado redirige al login.
    Uso: añade `if not require_login(): st.stop()` al inicio de cada página.

    Retorna True si la sesión está activa.
    """
    init_session()
    if not is_logged_in():
        st.warning("🔒 Necesitas iniciar sesión para acceder a esta sección.")
        st.stop()
    return True
