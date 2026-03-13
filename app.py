"""
app.py — Punto de entrada principal
Tarea 8 - Master Data Science / LaLiga Analytics
Streamlit >= 1.30

Para ejecutar:
    streamlit run app.py

Credenciales de prueba:
    Usuario     Contraseña      Rol
    ─────────   ───────────     ──────────
    admin       admin123        Administrador
    analista    laliga2024      Analista
    villarreal  ycf2024         Club
"""

import streamlit as st
from auth import init_session, login, logout, is_logged_in

# ---------------------------------------------------------------------------
# Configuración global (primera llamada a Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LaLiga Analytics | Master DS",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# CSS global
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Fondo general */
        .stApp { background-color: #0f1117; }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: #1a1d27;
            border-right: 1px solid #2e3250;
        }

        /* Ítem de navegación base */
        .nav-item {
            display: block;
            width: 100%;
            padding: 0.6rem 1rem;
            border-radius: 8px;
            margin-bottom: 0.3rem;
            color: #8892b0;
            font-size: 0.9rem;
            cursor: pointer;
            text-decoration: none;
            transition: background 0.15s;
        }
        .nav-item:hover  { background: #2e3250; color: #ccd6f6; }

        /* Ítem activo */
        .nav-item-active {
            background: #2e3250 !important;
            color: #64ffda !important;
            border-left: 3px solid #64ffda;
            font-weight: 600;
        }

        /* Tarjeta de login */
        .login-card {
            background: #1a1d27;
            border: 1px solid #2e3250;
            border-radius: 16px;
            padding: 2.5rem 2rem;
            max-width: 420px;
            margin: 0 auto;
        }
        .login-title {
            color: #ffffff;
            font-size: 1.8rem;
            font-weight: 700;
            text-align: center;
            margin-bottom: 0.25rem;
        }
        .login-subtitle {
            color: #8892b0;
            font-size: 0.9rem;
            text-align: center;
            margin-bottom: 1.5rem;
        }

        /* Botón logout */
        div[data-testid="stSidebar"] .stButton > button {
            width: 100%;
            background: #ff6b6b18;
            color: #ff6b6b;
            border: 1px solid #ff6b6b44;
            border-radius: 8px;
            margin-top: 0.5rem;
        }
        div[data-testid="stSidebar"] .stButton > button:hover {
            background: #ff6b6b33;
        }

        /* Ocultar menú y footer nativos */
        #MainMenu { visibility: hidden; }
        footer     { visibility: hidden; }

        /* Separador de sidebar */
        .sidebar-divider {
            border: none;
            border-top: 1px solid #2e3250;
            margin: 0.8rem 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Inicializar sesión y página por defecto
# ---------------------------------------------------------------------------
init_session()

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"


# ---------------------------------------------------------------------------
# ── SIDEBAR DE NAVEGACIÓN ──
# ---------------------------------------------------------------------------
PAGES = {
    "home":          ("🏠", "Inicio"),
    "estadisticas":  ("📊", "Estadísticas"),
    "fisico":        ("🏃", "Rendimiento Físico"),
}


def render_sidebar() -> None:
    """Dibuja el menú lateral con los ítems de navegación."""
    with st.sidebar:
        # Logo / título
        st.markdown(
            """
            <div style="padding:1rem 0.5rem 0.5rem 0.5rem; text-align:center;">
                <div style="font-size:2rem;">⚽</div>
                <div style="color:#ccd6f6; font-weight:700; font-size:1.05rem;
                            margin-top:0.2rem;">
                    LaLiga Analytics
                </div>
                <div style="color:#8892b0; font-size:0.75rem;">
                    Master Data Science · Tarea 8
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        # ── Menú de navegación ────────────────────────────────────────
        st.markdown(
            "<p style='color:#8892b0; font-size:0.75rem; "
            "text-transform:uppercase; letter-spacing:1px; "
            "padding-left:0.5rem; margin-bottom:0.5rem;'>Navegación</p>",
            unsafe_allow_html=True,
        )

        for page_id, (icon, label) in PAGES.items():
            active = (st.session_state.current_page == page_id)
            extra_class = "nav-item-active" if active else ""

            # Botón invisible sobre el HTML del ítem
            col_icon, col_btn = st.columns([0.15, 0.85])
            with col_btn:
                if st.button(
                    f"{icon}  {label}",
                    key=f"nav_{page_id}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                ):
                    st.session_state.current_page = page_id
                    st.rerun()

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        # ── Info de sesión ────────────────────────────────────────────
        info = st.session_state.user_info
        st.markdown(
            f"""
            <div style="padding:0.5rem; font-size:0.82rem; color:#8892b0;">
                <div>👤 <strong style="color:#ccd6f6;">
                    {st.session_state.username}
                </strong></div>
                <div style="margin-top:0.2rem;">
                    🎭 {info['rol'].capitalize()}
                    {f"&nbsp;·&nbsp; 🏟️ {info['equipo']}" if info.get('equipo') else ''}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        # ── Caché ─────────────────────────────────────────────────────
        from utils.cache_manager import render_cache_sidebar_widget
        render_cache_sidebar_widget()

        st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)

        # ── Botón logout ──────────────────────────────────────────────
        if st.button("🚪  Cerrar sesión", use_container_width=True):
            logout()
            st.session_state.current_page = "home"
            st.rerun()


# ---------------------------------------------------------------------------
# ── PÁGINA DE LOGIN ──
# ---------------------------------------------------------------------------
def render_login() -> None:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        st.markdown(
            """
            <div class="login-card">
                <div class="login-title">⚽ LaLiga Analytics</div>
                <div class="login-subtitle">Master Data Science · Tarea 8</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input(
                "👤 Usuario",
                placeholder="Introduce tu usuario",
                autocomplete="username",
            )
            password = st.text_input(
                "🔑 Contraseña",
                type="password",
                placeholder="Introduce tu contraseña",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button(
                "Iniciar sesión",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not username or not password:
                st.error("Por favor, introduce usuario y contraseña.")
            elif login(username, password):
                st.success("✅ Sesión iniciada. Cargando…")
                st.rerun()
            else:
                intentos = st.session_state.login_attempts
                st.error(f"❌ Credenciales incorrectas. Intento {intentos} de 5.")
                if intentos >= 5:
                    st.warning("⚠️ Demasiados intentos. Recarga la página.")
                    st.stop()

        with st.expander("ℹ️ Credenciales de prueba"):
            st.markdown(
                """
                | Usuario | Contraseña | Rol |
                |---|---|---|
                | `admin` | `admin123` | Administrador |
                | `analista` | `laliga2024` | Analista |
                | `villarreal` | `ycf2024` | Club |
                """
            )


# ---------------------------------------------------------------------------
# ── ROUTER PRINCIPAL ──
# ---------------------------------------------------------------------------
def main() -> None:
    if not is_logged_in():
        render_login()
        return

    # Usuario autenticado: mostrar sidebar + página activa
    render_sidebar()

    # Importar y renderizar la página correspondiente
    page = st.session_state.current_page

    if page == "home":
        from pages.home import render
        render()

    elif page == "estadisticas":
        from pages.estadisticas import render
        render()

    elif page == "fisico":
        from pages.fisico import render
        render()

    else:
        # Página no encontrada → volver al inicio
        st.session_state.current_page = "home"
        st.rerun()


if __name__ == "__main__":
    main()
