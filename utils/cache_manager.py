"""
utils/cache_manager.py — Gestión y monitorización del caché de Streamlit
=========================================================================
Centraliza toda la información sobre el caché de la aplicación y
proporciona herramientas para visualizarlo y controlarlo desde la UI.

Streamlit ofrece dos decoradores de caché:

  @st.cache_data      — Para datos serializables (DataFrames, listas, dicts…).
                        Cada sesión obtiene su propia copia del resultado.
                        Es el más usado en esta app.

  @st.cache_resource  — Para recursos compartidos entre sesiones
                        (conexiones BD, modelos ML, objetos pesados).
                        Todas las sesiones comparten el mismo objeto.
                        No usado en esta app porque SQLite + cache_data
                        es suficiente y más seguro en entornos multi-usuario.

Estrategia de TTL en esta aplicación:
  • Consultas SQLite    → TTL = 300 s  (5 min)   — datos locales estables
  • Consultas API       → TTL = 3600 s (1 hora)  — API con rate-limit
  • Listas auxiliares   → TTL = 600 s  (10 min)  — poco volátiles
"""

from __future__ import annotations
from datetime import datetime, timedelta
import streamlit as st


# ── Registro de funciones cacheadas ───────────────────────────────────────
# Sirve de "inventario" para el dashboard: qué está cacheado, cuánto dura y por qué.
CACHE_REGISTRY: list[dict] = [
    # ── Base de datos SQLite ──
    {
        "función":     "query_equipos_stats()",
        "módulo":      "data.database",
        "tipo":        "cache_data",
        "ttl_s":       300,
        "descripción": "Estadísticas avanzadas por equipo (tabla SQLite)",
        "origen":      "SQLite local",
    },
    {
        "función":     "query_rendimiento()",
        "módulo":      "data.database",
        "tipo":        "cache_data",
        "ttl_s":       300,
        "descripción": "Rendimiento físico por jugador (tabla SQLite)",
        "origen":      "SQLite local",
    },
    {
        "función":     "get_equipos_lista()",
        "módulo":      "data.database",
        "tipo":        "cache_data",
        "ttl_s":       600,
        "descripción": "Lista de equipos únicos",
        "origen":      "SQLite local",
    },
    {
        "función":     "get_jugadores_lista()",
        "módulo":      "data.database",
        "tipo":        "cache_data",
        "ttl_s":       600,
        "descripción": "Lista de jugadores únicos por equipo",
        "origen":      "SQLite local",
    },
    {
        "función":     "get_db_info()",
        "módulo":      "data.database",
        "tipo":        "cache_data",
        "ttl_s":       300,
        "descripción": "Metadatos de las tablas de la BD",
        "origen":      "SQLite local",
    },
    # ── API externa ──
    {
        "función":     "fetch_standings()",
        "módulo":      "data.api_client",
        "tipo":        "cache_data",
        "ttl_s":       3600,
        "descripción": "Clasificación LaLiga (football-data.org)",
        "origen":      "API externa",
    },
    {
        "función":     "fetch_matches()",
        "módulo":      "data.api_client",
        "tipo":        "cache_data",
        "ttl_s":       3600,
        "descripción": "Partidos LaLiga (football-data.org)",
        "origen":      "API externa",
    },
    {
        "función":     "fetch_team_list()",
        "módulo":      "data.api_client",
        "tipo":        "cache_data",
        "ttl_s":       3600,
        "descripción": "Listado de equipos (football-data.org)",
        "origen":      "API externa",
    },
]


def _ttl_label(ttl_s: int) -> str:
    """Convierte segundos en texto legible."""
    if ttl_s < 60:
        return f"{ttl_s} s"
    if ttl_s < 3600:
        return f"{ttl_s // 60} min"
    return f"{ttl_s // 3600} h"


def _ttl_bar(ttl_s: int, max_s: int = 3600) -> str:
    """Mini barra de progreso ASCII proporcional al TTL."""
    ratio = min(ttl_s / max_s, 1.0)
    filled = int(ratio * 10)
    return "█" * filled + "░" * (10 - filled)


# ── API pública ────────────────────────────────────────────────────────────

def clear_all_cache() -> None:
    """
    Invalida toda la caché de st.cache_data.
    La próxima llamada a cualquier función cacheada recalculará su resultado.
    """
    st.cache_data.clear()


def render_cache_dashboard() -> None:
    """
    Renderiza el dashboard de caché con:
      - Explicación de la estrategia
      - Tabla con todas las funciones cacheadas
      - Botón para limpiar la caché
      - Métricas visuales
    """
    st.subheader("⚡ Optimización con caché de Streamlit")

    # ── Explicación conceptual ────────────────────────────────────────────
    with st.expander("📚 ¿Cómo funciona el caché en esta app?", expanded=False):
        st.markdown(
            """
            Streamlit ofrece dos mecanismos de caché que se aplican como
            **decoradores** sobre funciones Python:

            | Decorador | Ámbito | Uso en esta app |
            |---|---|---|
            | `@st.cache_data` | Por sesión · copia independiente | ✅ Consultas SQL y API |
            | `@st.cache_resource` | Global · objeto compartido | ⬜ No necesario (SQLite local) |

            **Estrategia de TTL:**
            - **Consultas SQLite (5 min):** Los datos del Excel son estáticos;
              5 minutos es un compromiso entre frescura y rendimiento.
            - **Listas auxiliares (10 min):** Los equipos y jugadores apenas cambian.
            - **API externa (1 hora):** Respeta el rate-limit del plan gratuito
              (100 llamadas/día) y evita latencia repetida.

            **Beneficio medible:** sin caché, cada interacción del usuario relanza
            la consulta SQL o la petición HTTP. Con caché, el tiempo de respuesta
            pasa de ~500 ms a < 5 ms para datos ya almacenados.
            """
        )

    # ── Métricas de configuración ─────────────────────────────────────────
    sql_items = [r for r in CACHE_REGISTRY if r["origen"] == "SQLite local"]
    api_items = [r for r in CACHE_REGISTRY if r["origen"] == "API externa"]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🗄️ Funciones cacheadas", len(CACHE_REGISTRY))
    c2.metric("📊 Caché SQL (TTL)",      "5–10 min")
    c3.metric("🌐 Caché API (TTL)",      "1 hora")
    c4.metric("💡 Tipo utilizado",       "cache_data")

    st.divider()

    # ── Tabla de inventario ───────────────────────────────────────────────
    st.markdown("##### 🗂️ Inventario de funciones cacheadas")

    import pandas as pd
    rows = []
    for item in CACHE_REGISTRY:
        ttl = item["ttl_s"]
        rows.append({
            "Función":      item["función"],
            "Tipo":         f'@st.{item["tipo"]}',
            "TTL":          _ttl_label(ttl),
            "Barra TTL":    _ttl_bar(ttl),
            "Origen":       item["origen"],
            "Descripción":  item["descripción"],
        })

    df_cache = pd.DataFrame(rows)
    st.dataframe(
        df_cache,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Barra TTL": st.column_config.TextColumn("Duración relativa"),
        },
    )

    st.divider()

    # ── Control de caché ──────────────────────────────────────────────────
    st.markdown("##### 🧹 Control manual del caché")
    col_btn, col_info = st.columns([1, 3])

    with col_btn:
        if st.button("🔄 Limpiar toda la caché", type="primary",
                     use_container_width=True):
            clear_all_cache()
            st.success("✅ Caché limpiada. Los próximos accesos recalcularán los datos.")
            st.info(
                "ℹ️ Esto fuerza la reconsulta desde SQLite y la API en el "
                "siguiente acceso de cada función."
            )

    with col_info:
        st.markdown(
            """
            > **¿Cuándo limpiar la caché?**
            > - Tras actualizar los ficheros Excel de datos
            > - Si los datos de la API parecen desactualizados
            > - Para forzar la recarga después de cambios en la BD

            El caché se limpia automáticamente al reiniciar la aplicación
            o cuando expira el TTL de cada función.
            """
        )


def render_cache_sidebar_widget() -> None:
    """
    Widget compacto para el sidebar: muestra el estado y un botón de limpieza.
    """
    st.markdown(
        "<p style='color:#8892b0; font-size:0.75rem; text-transform:uppercase;"
        "letter-spacing:1px; margin-bottom:0.4rem;'>Caché</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown(
            f"<span style='color:#4ecdc4; font-size:0.8rem;'>"
            f"⚡ {len(CACHE_REGISTRY)} funciones activas</span>",
            unsafe_allow_html=True,
        )
    with col2:
        if st.button("🔄 Limpiar", key="sidebar_clear_cache",
                     use_container_width=True):
            clear_all_cache()
            st.success("Caché limpiada")
            st.rerun()
