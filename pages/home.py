"""
pages/home.py — Página de inicio / Dashboard principal
"""

import streamlit as st
from utils.cache_manager import render_cache_dashboard


def render() -> None:
    info   = st.session_state.user_info
    nombre = info["nombre"]
    rol    = info["rol"]
    equipo = info.get("equipo")

    # ── Banner de bienvenida ─────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(135deg, #1a1d27 0%, #2e3250 100%);
            border: 1px solid #3d4f7c;
            border-radius: 12px;
            padding: 1.5rem 2rem;
            margin-bottom: 1.5rem;
        ">
            <h2 style="color:#ccd6f6; margin:0;">👋 ¡Bienvenido, {nombre}!</h2>
            <p style="color:#8892b0; margin:0.4rem 0 0 0;">
                Sesión activa como <strong>{rol}</strong>
                {f'&nbsp;·&nbsp;Club: <strong>{equipo}</strong>' if equipo else ''}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Métricas rápidas ─────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👤 Usuario",          st.session_state.username)
    c2.metric("🎭 Rol",              rol.capitalize())
    c3.metric("📂 Fuentes de datos", "2")
    c4.metric("🟢 Sesión",           "Activa")

    st.divider()

    # ── Módulos disponibles ──────────────────────────────────────────────
    st.subheader("📂 Módulos de la aplicación")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="background:#1a1d27; border:1px solid #2e3250;
                        border-radius:12px; padding:1.2rem 1.5rem;">
                <h4 style="color:#ccd6f6; margin:0 0 0.5rem 0;">
                    📊 Estadísticas de Equipos
                </h4>
                <p style="color:#8892b0; font-size:0.85rem; margin:0;">
                    167 métricas avanzadas · StatsBomb · SQLite + API
                </p>
                <p style="color:#4ecdc4; font-size:0.8rem; margin:0.6rem 0 0 0;">
                    ✅ Gráficos interactivos · Exportar PDF · Imprimir
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="background:#1a1d27; border:1px solid #2e3250;
                        border-radius:12px; padding:1.2rem 1.5rem;">
                <h4 style="color:#ccd6f6; margin:0 0 0.5rem 0;">
                    🏃 Rendimiento Físico
                </h4>
                <p style="color:#8892b0; font-size:0.85rem; margin:0;">
                    Datos por jugador · Jornada a jornada · SQLite + API
                </p>
                <p style="color:#4ecdc4; font-size:0.8rem; margin:0.6rem 0 0 0;">
                    ✅ Gráficos interactivos · Exportar PDF · Imprimir
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Fuentes de datos ─────────────────────────────────────────────────
    st.subheader("🗂️ Fuentes de datos")
    with st.expander("Ver detalle de archivos y conexiones"):
        st.markdown(
            """
            | Fuente | Tipo | Módulo | Tabla / Endpoint |
            |---|---|---|---|
            | `TeamStats1a_Statsbomb_24_25.xlsx` | Excel → SQLite | `data.database` | `equipos_stats` |
            | `LaLigaRendimiento2024_2025.xlsm` | Excel → SQLite | `data.database` | `rendimiento_fisico` |
            | football-data.org | API REST v4 | `data.api_client` | `/competitions/PD/standings` |
            | football-data.org | API REST v4 | `data.api_client` | `/competitions/PD/matches` |
            """
        )

    st.divider()

    # ── Dashboard de caché (Punto 1e) ────────────────────────────────────
    render_cache_dashboard()

    st.divider()

    # ── Guía de despliegue (Punto 1e) ────────────────────────────────────
    st.subheader("🚀 Publicación de la aplicación")

    tab_sc, tab_render, tab_local = st.tabs([
        "☁️ Streamlit Community Cloud",
        "🟣 Render",
        "🖥️ Local / LAN",
    ])

    with tab_sc:
        st.markdown(
            """
            **Streamlit Community Cloud** es la plataforma oficial y gratuita.
            Solo necesitas una cuenta de GitHub.

            **Pasos:**

            **1. Sube el código a GitHub**
            ```bash
            git init && git add .
            git commit -m "LaLiga Analytics - Tarea 8"
            git remote add origin https://github.com/<usuario>/<repo>.git
            git push -u origin main
            ```

            **2.** Entra en **[share.streamlit.io](https://share.streamlit.io)**
            e inicia sesión con GitHub.

            **3.** Haz clic en **"New app"** y rellena:
            - Repository: `<usuario>/<repo>`
            - Branch: `main`
            - Main file path: `app/app.py`

            **4.** En **"Advanced settings → Secrets"** añade:
            ```toml
            FOOTBALL_API_KEY = "tu_api_key_aqui"
            ```

            **5.** Pulsa **"Deploy"** — URL pública:
            ```
            https://<usuario>-<repo>-app.streamlit.app
            ```

            > ⚠️ El `.gitignore` ya excluye `secrets.toml` y `laliga.db`
            > para que no se suban datos sensibles ni la BD local.
            """
        )

    with tab_render:
        st.markdown(
            """
            [**Render**](https://render.com) permite desplegar con más recursos
            en su plan gratuito.

            **Pasos:**

            1. Sube el código a GitHub (igual que arriba).
            2. En render.com → **New Web Service** → conecta el repo.
            3. Configura:
               - **Build:** `pip install -r app/requirements.txt`
               - **Start:** `streamlit run app/app.py --server.port $PORT --server.address 0.0.0.0`
            4. Añade la variable de entorno `FOOTBALL_API_KEY`.

            > El plan gratuito hiberna la app tras 15 min de inactividad.
            """
        )

    with tab_local:
        st.markdown(
            """
            Para compartir en red local sin publicar en internet:

            ```bash
            streamlit run app.py --server.address 0.0.0.0 --server.port 8501
            ```

            Otros usuarios en la misma WiFi acceden en:
            ```
            http://<tu-ip-local>:8501
            ```

            Para ver tu IP local:
            ```bash
            # macOS / Linux
            ifconfig | grep "inet " | grep -v 127.0.0.1
            # Windows
            ipconfig
            ```
            """
        )
