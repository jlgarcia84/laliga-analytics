"""
pages/fisico.py — Rendimiento Físico de Jugadores
Fuente 1 → SQLite  |  Fuente 2 → API football-data.org
Incluye: visualizaciones Plotly, botón imprimir, exportar a PDF
"""

import streamlit as st
from data.database import (
    query_rendimiento, get_equipos_fisico_lista, get_jugadores_lista,
    get_db_info, init_database, query_evolucion_jugador,
)
from data.api_client import render_api_key_input, fetch_matches
from utils.charts import (
    chart_top_jugadores, chart_demarcacion_box, chart_evolucion_jornada,
)
from utils.print_utils import inject_print_css, render_print_button
from utils.pdf_export import generate_pdf_fisico


def render() -> None:
    inject_print_css()

    st.title("🏃 Rendimiento Físico")
    st.caption("LaLiga 2024/25 · Datos por jugador · SQLite + API")

    # ── Barra de acciones ────────────────────────────────────────────────
    st.divider()
    col_a1, col_a2, col_a3 = st.columns([1, 1, 5])
    with col_a1:
        render_print_button("🖨️ Imprimir")
    with col_a2:
        export_pdf_clicked = st.button("📄 Exportar PDF", key="pdf_fisico")

    st.divider()

    tab1, tab2 = st.tabs([
        "🗄️  Fuente 1 · Base de Datos SQL (SQLite)",
        "🌐  Fuente 2 · API Externa (football-data.org)",
    ])

    # ════════════════════════════════════════════════════════════════════
    # FUENTE 1 — SQLite
    # ════════════════════════════════════════════════════════════════════
    with tab1:
        st.subheader("🗄️ Datos físicos desde SQLite")

        with st.expander("ℹ️ Detalles de la conexión SQL", expanded=False):
            st.markdown("""
            | Parámetro | Valor |
            |---|---|
            | **Motor** | SQLite 3 (stdlib Python) |
            | **Fichero** | `app/laliga.db` |
            | **Tabla** | `rendimiento_fisico` |
            | **Caché** | `@st.cache_data` · TTL 5 min |
            | **Origen** | `LaLigaRendimiento2024_2025.xlsm` · Hoja "Físico" |
            """)

        init_database()
        try:
            db_info = get_db_info()
            c1, c2, c3 = st.columns(3)
            c1.metric("📝 Registros en BD", f"{db_info['rendimiento_fisico']['filas']:,}")
            c2.metric("📐 Variables",        db_info["rendimiento_fisico"]["columnas"])
            c3.metric("📅 Temporada",        "2024/25")
        except Exception:
            pass

        st.divider()

        # ── Filtros ──────────────────────────────────────────────────────
        st.markdown("##### 🔍 Filtros")
        col1, col2, col3 = st.columns(3)

        with col1:
            try:
                # Usar equipos de rendimiento_fisico para que los nombres coincidan
                equipos = ["Todos"] + get_equipos_fisico_lista()
            except Exception:
                equipos = ["Todos"]
            equipo_sel = st.selectbox("🏟️ Equipo:", equipos, key="eq_fisico")

        with col2:
            try:
                jugadores = ["Todos"] + get_jugadores_lista(
                    equipo_sel if equipo_sel != "Todos" else None
                )
            except Exception:
                jugadores = ["Todos"]
            jugador_sel = st.selectbox("👤 Jugador:", jugadores, key="jug_fisico")

        with col3:
            limite = st.slider(
                "Máx. registros:", 50, 500, 200, step=50, key="lim_fisico"
            )

        # Filtro de jornadas (rango)
        col4, col5 = st.columns(2)
        with col4:
            jornada_min = st.number_input(
                "📅 Jornada desde:", min_value=1, max_value=38, value=1,
                step=1, key="jornada_min"
            )
        with col5:
            jornada_max = st.number_input(
                "📅 Jornada hasta:", min_value=1, max_value=38, value=38,
                step=1, key="jornada_max"
            )
        if jornada_min > jornada_max:
            st.warning("⚠️ La jornada inicial no puede ser mayor que la final.")
            jornada_min, jornada_max = 1, 38

        # ── Consulta ─────────────────────────────────────────────────────
        try:
            with st.spinner("Consultando base de datos…"):
                df = query_rendimiento(equipo_sel, jugador_sel, limite)
                # Aplicar filtro de jornadas sobre el resultado
                if "Jornada" in df.columns:
                    df = df[
                        (df["Jornada"] >= jornada_min) &
                        (df["Jornada"] <= jornada_max)
                    ]
        except Exception as e:
            st.error(f"Error BD: {e}")
            return

        if df.empty:
            st.warning("Sin datos para los filtros seleccionados.")
            return

        # SQL mostrada
        where_parts = []
        if equipo_sel != "Todos":
            where_parts.append(f'Equipo = "{equipo_sel}"')
        if jugador_sel != "Todos":
            where_parts.append(f'Alias = "{jugador_sel}"')
        where = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""
        with st.expander("🔎 Consulta SQL ejecutada"):
            st.code(
                f"SELECT * FROM rendimiento_fisico\n{where}\nLIMIT {limite};",
                language="sql",
            )

        # ── Tabla ─────────────────────────────────────────────────────────
        st.subheader("📋 Tabla de datos")
        cols_base  = ["Jornada", "Equipo", "Nombre", "Apellido", "Alias",
                      "Demarcacion", "Minutos jugados"]
        cols_extra = [c for c in df.columns if c not in cols_base]

        with st.expander("⚙️ Columnas adicionales"):
            cols_extra_sel = st.multiselect(
                "Añadir columnas:",
                cols_extra,
                default=cols_extra[:5] if len(cols_extra) >= 5 else cols_extra,
                key="cols_fisico",
            )

        cols_show = [c for c in cols_base if c in df.columns] + cols_extra_sel
        st.dataframe(
            df[cols_show].reset_index(drop=True),
            use_container_width=True,
            height=320,
        )
        st.caption(
            f"📊 {len(df):,} registros · {len(cols_show)} columnas · Caché TTL 5 min"
        )

        st.divider()

        # ════════════════════════════════════════════════════════════════
        # VISUALIZACIONES
        # ════════════════════════════════════════════════════════════════
        st.subheader("📈 Visualizaciones")

        # Fila 1: top jugadores + box demarcación
        v1, v2 = st.columns(2)
        with v1:
            st.plotly_chart(chart_top_jugadores(df, top_n=15), use_container_width=True)
        with v2:
            st.plotly_chart(chart_demarcacion_box(df), use_container_width=True)

        # Gráfico de evolución — siempre consulta TODAS las jornadas del jugador
        st.markdown("##### 📈 Evolución temporal de un jugador")
        if "Alias" in df.columns:
            jugadores_disp = sorted(df["Alias"].dropna().unique().tolist())
            if jugadores_disp:
                # Si ya hay un jugador seleccionado en el filtro, usarlo por defecto
                default_idx = (
                    jugadores_disp.index(jugador_sel)
                    if jugador_sel != "Todos" and jugador_sel in jugadores_disp
                    else 0
                )
                jug_evo = st.selectbox(
                    "Selecciona jugador para ver su evolución:",
                    jugadores_disp,
                    index=default_idx,
                    key="jug_evo",
                )
                # Consulta independiente con TODAS las jornadas (sin límite ni caché)
                df_evo = query_evolucion_jugador(jug_evo)
                st.caption(f"🔍 Debug: {len(df_evo)} jornadas encontradas para {jug_evo}")
                st.plotly_chart(
                    chart_evolucion_jornada(df_evo, jug_evo),
                    use_container_width=True,
                )

        # ── Exportar PDF ─────────────────────────────────────────────────
        if export_pdf_clicked:
            with st.spinner("Generando PDF…"):
                try:
                    usuario = st.session_state.get("username", "analista")
                    pdf_bytes = generate_pdf_fisico(df, equipo_sel, jugador_sel, usuario)
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"fisico_{equipo_sel.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key="dl_pdf_fisico",
                    )
                    st.success("✅ PDF generado. Haz clic en '⬇️ Descargar PDF' para guardarlo.")
                except Exception as e:
                    st.error(f"Error al generar el PDF: {e}")

    # ════════════════════════════════════════════════════════════════════
    # FUENTE 2 — API
    # ════════════════════════════════════════════════════════════════════
    with tab2:
        st.subheader("🌐 Calendario de partidos desde API")

        with st.expander("ℹ️ Detalles de la conexión API", expanded=False):
            st.markdown("""
            | Parámetro | Valor |
            |---|---|
            | **Endpoint** | `GET /v4/competitions/PD/matches` |
            | **Status** | `SCHEDULED` / `FINISHED` |
            | **Caché** | `@st.cache_data` · TTL 1 hora |
            """)

        api_key = render_api_key_input()
        if not api_key:
            return

        st.divider()

        tipo = st.radio(
            "Tipo de partidos:",
            ["🔜 Próximos", "✅ Disputados"],
            horizontal=True,
            key="tipo_p",
        )
        status = {"🔜 Próximos": "SCHEDULED", "✅ Disputados": "FINISHED"}[tipo]

        with st.spinner("Consultando API…"):
            df_m = fetch_matches(api_key, status=status)

        if df_m is not None and not df_m.empty:
            st.dataframe(df_m, use_container_width=True, height=420,
                         column_config={
                             "Resultado": st.column_config.TextColumn(width="small"),
                             "Jornada":   st.column_config.NumberColumn(width="small"),
                         })
            st.caption(f"🌐 {len(df_m)} partidos · Caché 1 hora")

            # Gráfico de goles por partido (solo disputados)
            if status == "FINISHED" and "Resultado" in df_m.columns:
                import plotly.graph_objects as go
                resultados = df_m["Resultado"].str.extract(r"(\d+)\s*-\s*(\d+)")
                if resultados is not None and not resultados.empty:
                    df_m = df_m.copy()
                    df_m["Goles total"] = (
                        resultados[0].astype(float, errors="ignore") +
                        resultados[1].astype(float, errors="ignore")
                    )
                    lbl = df_m["Local"].str.split().str[-1] + " vs " + \
                          df_m["Visitante"].str.split().str[-1]
                    fig = go.Figure(go.Bar(
                        x=lbl,
                        y=df_m["Goles total"],
                        marker_color="#64ffda",
                    ))
                    fig.update_layout(
                        title="⚽ Goles totales por partido",
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(26,29,39,0.6)",
                        height=360,
                        xaxis_tickangle=-35,
                        margin=dict(l=10, r=10, t=40, b=80),
                        font=dict(color="#ccd6f6"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

        elif df_m is not None:
            st.info(f"No hay partidos con estado '{status}' disponibles.")
