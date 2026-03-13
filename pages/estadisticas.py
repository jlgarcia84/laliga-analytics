"""
pages/estadisticas.py — Estadísticas de Equipos
Fuente 1 → SQLite  |  Fuente 2 → API football-data.org
Incluye: visualizaciones Plotly, botón imprimir, exportar a PDF
"""

import streamlit as st
from data.database import (
    query_equipos_stats, get_equipos_lista, get_db_info, init_database,
)
from data.api_client import (
    render_api_key_input, fetch_standings, fetch_matches, fetch_team_list,
)
from utils.charts import (
    chart_goles, chart_xg_scatter, chart_posesion, chart_tiros,
    chart_equipo_radar,
)
from utils.print_utils import inject_print_css, render_print_button
from utils.pdf_export import generate_pdf_estadisticas


def render() -> None:
    # Inyectar CSS de impresión al inicio de la página
    inject_print_css()

    st.title("📊 Estadísticas de Equipos")
    st.caption("LaLiga 2024/25 · Datos avanzados StatsBomb + API football-data.org")

    # ── Barra de acciones (imprimir / exportar PDF) ──────────────────────
    st.divider()
    col_acc1, col_acc2, col_acc3 = st.columns([1, 1, 5])

    with col_acc1:
        render_print_button("🖨️ Imprimir")

    with col_acc2:
        # Placeholder: el botón PDF se activa tras cargar datos
        export_pdf_clicked = st.button("📄 Exportar PDF", key="pdf_stats")

    st.divider()

    # ── Pestañas de fuentes de datos ─────────────────────────────────────
    tab1, tab2 = st.tabs([
        "🗄️  Fuente 1 · Base de Datos SQL (SQLite)",
        "🌐  Fuente 2 · API Externa (football-data.org)",
    ])

    # ════════════════════════════════════════════════════════════════════
    # FUENTE 1 — SQLite
    # ════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("🗄️ Conexión a base de datos SQLite")

        with st.expander("ℹ️ Detalles de la conexión SQL", expanded=False):
            st.markdown("""
            | Parámetro | Valor |
            |---|---|
            | **Motor** | SQLite 3 (stdlib Python) |
            | **Fichero** | `app/laliga.db` |
            | **Tabla** | `equipos_stats` |
            | **Caché** | `@st.cache_data` · TTL 5 min |
            | **Origen** | `TeamStats1a_Statsbomb_24_25.xlsx` |
            """)

        # Inicializar BD y mostrar métricas
        init_database()
        try:
            db_info = get_db_info()
            c1, c2, c3 = st.columns(3)
            c1.metric("🏟️ Equipos",   db_info["equipos_stats"]["filas"])
            c2.metric("📐 Variables",  db_info["equipos_stats"]["columnas"])
            c3.metric("📅 Temporada",  "2024/25")
        except Exception:
            pass

        st.divider()

        # ── Filtros ──────────────────────────────────────────────────────
        col_eq, col_cat = st.columns([1, 2])
        with col_eq:
            try:
                equipos = ["Todos"] + get_equipos_lista()
            except Exception:
                equipos = ["Todos"]
            equipo_sel = st.selectbox("🏟️ Equipo:", equipos, key="eq_sql")

        with col_cat:
            categorias = {
                "⚽ Goles y xG":   lambda c: [x for x in c if "gol" in x.lower() or "xg" in x.lower()],
                "🎯 Tiros":        lambda c: [x for x in c if "tiro" in x.lower()],
                "🔄 Pases":        lambda c: [x for x in c if "pase" in x.lower() or "centro" in x.lower()],
                "🛡️ Presiones":    lambda c: [x for x in c if "presion" in x.lower() or "recuper" in x.lower()],
                "📋 Todas":        lambda c: c,
            }
            cat_sel = st.selectbox("📂 Categoría:", list(categorias.keys()), key="cat_sql")

        # ── Cargar datos ─────────────────────────────────────────────────
        try:
            with st.spinner("Consultando base de datos…"):
                df = query_equipos_stats(equipo_sel)
        except Exception as e:
            st.error(f"Error BD: {e}")
            return

        if df.empty:
            st.warning("Sin datos para los filtros seleccionados.")
            return

        # Columnas filtradas por categoría
        base = ["Equipo", "Partidos"]
        filt = categorias[cat_sel](list(df.columns))
        cols_mostrar = base + [c for c in filt if c not in base]

        with st.expander("🔎 Consulta SQL ejecutada"):
            where_sql = f'WHERE Equipo = "{equipo_sel}"' if equipo_sel != "Todos" else ""
            cols_preview = ", ".join(cols_mostrar[:5]) + ("..." if len(cols_mostrar) > 5 else "")
            st.code(
                f"SELECT {cols_preview}\nFROM equipos_stats\n{where_sql}\nORDER BY Equipo;",
                language="sql",
            )

        # ── Tabla de datos ────────────────────────────────────────────────
        st.subheader("📋 Tabla de datos")
        st.dataframe(
            df[cols_mostrar].reset_index(drop=True),
            use_container_width=True,
            height=320,
        )
        st.caption(f"📊 {len(df)} equipo(s) · {len(cols_mostrar)} columnas · Caché TTL 5 min")

        st.divider()

        # ════════════════════════════════════════════════════════════════
        # VISUALIZACIONES
        # ════════════════════════════════════════════════════════════════
        st.subheader("📈 Visualizaciones")

        # Fila 1: goles + xG scatter
        v1, v2 = st.columns(2)
        with v1:
            st.plotly_chart(chart_goles(df), use_container_width=True)
        with v2:
            st.plotly_chart(chart_xg_scatter(df), use_container_width=True)

        # Fila 2: posesión + tiros
        v3, v4 = st.columns(2)
        with v3:
            st.plotly_chart(chart_posesion(df), use_container_width=True)
        with v4:
            st.plotly_chart(chart_tiros(df), use_container_width=True)

        # Radar para equipo concreto
        if equipo_sel != "Todos":
            st.plotly_chart(
                chart_equipo_radar(df, equipo_sel),
                use_container_width=True,
            )

        # ── Exportar PDF ─────────────────────────────────────────────────
        if export_pdf_clicked:
            with st.spinner("Generando PDF…"):
                try:
                    usuario = st.session_state.get("username", "analista")
                    pdf_bytes = generate_pdf_estadisticas(df, equipo_sel, usuario)
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"estadisticas_{equipo_sel.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key="dl_pdf_stats",
                    )
                    st.success("✅ PDF generado. Haz clic en '⬇️ Descargar PDF' para guardarlo.")
                except Exception as e:
                    st.error(f"Error al generar el PDF: {e}")

    # ════════════════════════════════════════════════════════════════════
    # FUENTE 2 — API football-data.org
    # ════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("🌐 Conexión a API externa · football-data.org")

        with st.expander("ℹ️ Detalles de la conexión API", expanded=False):
            st.markdown("""
            | Parámetro | Valor |
            |---|---|
            | **Proveedor** | [football-data.org](https://www.football-data.org) |
            | **Versión** | v4 |
            | **Competición** | La Liga · `PD` |
            | **Autenticación** | Header `X-Auth-Token` |
            | **Caché** | `@st.cache_data` · TTL 1 hora |
            """)

        api_key = render_api_key_input()
        if not api_key:
            return

        st.divider()

        sub1, sub2, sub3 = st.tabs([
            "🏆 Clasificación", "📅 Partidos recientes", "🏟️ Equipos"
        ])

        with sub1:
            st.markdown("##### Clasificación LaLiga 2024/25")
            with st.spinner("Consultando API…"):
                df_st = fetch_standings(api_key)
            if df_st is not None and not df_st.empty:
                st.dataframe(df_st, use_container_width=True, height=420,
                             column_config={
                                 "Pos": st.column_config.NumberColumn(width="small"),
                                 "Pts": st.column_config.NumberColumn(width="small"),
                             })
                st.caption(f"🌐 {len(df_st)} equipos · Caché 1 hora")

                # Mini gráfico de clasificación con Plotly
                if df_st is not None and "Equipo" in df_st.columns:
                    import plotly.express as px
                    fig_pts = px.bar(
                        df_st.sort_values("Pts"),
                        x="Pts", y="Equipo", orientation="h",
                        color="Pts", color_continuous_scale="Teal",
                        template="plotly_dark",
                        title="🏆 Puntos por equipo · LaLiga",
                    )
                    fig_pts.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(26,29,39,0.6)",
                        height=500,
                        showlegend=False,
                        margin=dict(l=10, r=10, t=40, b=10),
                    )
                    fig_pts.update_coloraxes(showscale=False)
                    st.plotly_chart(fig_pts, use_container_width=True)

        with sub2:
            st.markdown("##### Últimos partidos")
            with st.spinner("Consultando API…"):
                df_m = fetch_matches(api_key, status="FINISHED")
            if df_m is not None and not df_m.empty:
                st.dataframe(df_m, use_container_width=True, height=380)
                st.caption(f"🌐 {len(df_m)} partidos · Caché 1 hora")

        with sub3:
            st.markdown("##### Equipos de LaLiga")
            with st.spinner("Consultando API…"):
                df_teams = fetch_team_list(api_key)
            if df_teams is not None and not df_teams.empty:
                st.dataframe(df_teams, use_container_width=True, height=380)
                st.caption(f"🌐 {len(df_teams)} equipos · Caché 1 hora")
