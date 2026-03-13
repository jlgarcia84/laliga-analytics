"""
utils/charts.py — Visualizaciones interactivas con Plotly
==========================================================
Todas las funciones devuelven un objeto go.Figure listo para mostrar
con st.plotly_chart(fig, use_container_width=True).

Tema: plotly_dark  — coherente con el diseño oscuro de la aplicación.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Paleta y tema globales ────────────────────────────────────────────────
THEME  = "plotly_dark"
SEQ    = px.colors.sequential.Teal          # escala secuencial (azul-verde)
QUAL   = px.colors.qualitative.Bold         # colores cualitativos
ACCENT = "#64ffda"                          # verde menta de la app
RED    = "#ff6b6b"
BG     = "rgba(0,0,0,0)"                    # fondo transparente

_LAYOUT = dict(
    paper_bgcolor=BG,
    plot_bgcolor="rgba(26,29,39,0.6)",
    font=dict(family="Inter, sans-serif", color="#ccd6f6"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)


# ══════════════════════════════════════════════════════════════════════════
# ESTADÍSTICAS DE EQUIPOS
# ══════════════════════════════════════════════════════════════════════════

def chart_goles(df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras agrupadas: Goles a favor vs Goles en contra
    por equipo, ordenados por GF descendente.
    """
    needed = {"Equipo", "Goles a favor", "Goles en contra"}
    if not needed.issubset(df.columns):
        return _empty_fig("Columnas de goles no disponibles")

    df_plot = df[["Equipo", "Goles a favor", "Goles en contra"]].copy()
    df_plot = df_plot.sort_values("Goles a favor", ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df_plot["Equipo"],
        x=df_plot["Goles a favor"],
        name="Goles a favor",
        orientation="h",
        marker_color=ACCENT,
    ))
    fig.add_trace(go.Bar(
        y=df_plot["Equipo"],
        x=df_plot["Goles en contra"],
        name="Goles en contra",
        orientation="h",
        marker_color=RED,
    ))

    fig.update_layout(
        **_LAYOUT,
        title="⚽ Goles a favor vs en contra por equipo",
        barmode="group",
        xaxis_title="Goles",
        height=520,
    )
    return fig


def chart_xg_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot: xG esperados vs Goles reales.
    Los equipos por encima de la diagonal convierten más de lo esperado
    (sobrerendimiento); los de abajo, menos (infrarendimiento).
    """
    needed = {"Equipo", "xG (Sin Pen.) a favor", "Goles a favor"}
    if not needed.issubset(df.columns):
        return _empty_fig("Columnas de xG no disponibles")

    df_plot = df[["Equipo", "xG (Sin Pen.) a favor", "Goles a favor"]].copy()
    df_plot["Delta"] = df_plot["Goles a favor"] - df_plot["xG (Sin Pen.) a favor"]

    # Línea diagonal de referencia (xG == Goles)
    max_val = max(df_plot["xG (Sin Pen.) a favor"].max(),
                  df_plot["Goles a favor"].max()) + 2

    fig = go.Figure()

    # Línea de referencia
    fig.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val],
        mode="lines",
        line=dict(color="#8892b0", dash="dash", width=1),
        name="xG = Goles",
        showlegend=True,
    ))

    # Puntos de equipos, coloreados por Delta
    fig.add_trace(go.Scatter(
        x=df_plot["xG (Sin Pen.) a favor"],
        y=df_plot["Goles a favor"],
        mode="markers+text",
        text=df_plot["Equipo"].apply(lambda e: e.split()[-1]),  # apellido
        textposition="top center",
        textfont=dict(size=9, color="#ccd6f6"),
        marker=dict(
            size=12,
            color=df_plot["Delta"],
            colorscale="RdYlGn",
            cmin=-5, cmax=5,
            showscale=True,
            colorbar=dict(title="Δ (Goles−xG)", tickfont=dict(color="#ccd6f6")),
        ),
        name="Equipos",
        hovertemplate=(
            "<b>%{text}</b><br>"
            "xG: %{x:.1f}<br>Goles: %{y}<br>Δ: %{marker.color:+.1f}<extra></extra>"
        ),
    ))

    fig.update_layout(
        **_LAYOUT,
        title="🎯 xG esperados vs Goles reales (sobrerendimiento / infrarendimiento)",
        xaxis_title="xG (Sin Pen.) a favor",
        yaxis_title="Goles a favor",
        height=480,
    )
    return fig


def chart_posesion(df: pd.DataFrame) -> go.Figure:
    """
    Barras horizontales: % de posesión por equipo (ranking).
    """
    col = "% posesión"
    if col not in df.columns or "Equipo" not in df.columns:
        return _empty_fig("Columna '% posesión' no disponible")

    df_plot = df[["Equipo", col]].copy().dropna()
    df_plot = df_plot.sort_values(col, ascending=True)

    fig = px.bar(
        df_plot,
        x=col, y="Equipo",
        orientation="h",
        color=col,
        color_continuous_scale=SEQ,
        template=THEME,
        title="🔵 Ranking de posesión (%)",
    )
    fig.update_coloraxes(showscale=False)
    fig.update_layout(**_LAYOUT, height=500, xaxis_title="% Posesión")
    return fig


def chart_tiros(df: pd.DataFrame) -> go.Figure:
    """
    Scatter: Tiros a favor vs Tiros en contra por equipo.
    Permite ver el balance ofensivo-defensivo.
    """
    needed = {"Equipo", "Tiros a favor", "Tiros en contra"}
    if not needed.issubset(df.columns):
        return _empty_fig("Columnas de tiros no disponibles")

    df_plot = df[["Equipo", "Tiros a favor", "Tiros en contra"]].copy()
    avg_x = df_plot["Tiros a favor"].mean()
    avg_y = df_plot["Tiros en contra"].mean()

    fig = go.Figure()

    # Líneas de media (cuadrantes)
    for x_val, mode in [(avg_x, "vertical"), (avg_y, "horizontal")]:
        if mode == "vertical":
            fig.add_vline(x=x_val, line_dash="dot", line_color="#8892b0",
                          annotation_text="Media", annotation_position="top")
        else:
            fig.add_hline(y=x_val, line_dash="dot", line_color="#8892b0")

    fig.add_trace(go.Scatter(
        x=df_plot["Tiros a favor"],
        y=df_plot["Tiros en contra"],
        mode="markers+text",
        text=df_plot["Equipo"].apply(lambda e: e.split()[-1]),
        textposition="top center",
        textfont=dict(size=9),
        marker=dict(size=11, color=ACCENT, line=dict(color="#ffffff", width=1)),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Tiros favor: %{x}<br>Tiros contra: %{y}<extra></extra>"
        ),
    ))

    fig.update_layout(
        **_LAYOUT,
        title="🎯 Tiros a favor vs en contra",
        xaxis_title="Tiros a favor", yaxis_title="Tiros en contra",
        height=460,
        annotations=[
            dict(x=avg_x + 10, y=df_plot["Tiros en contra"].min(),
                 text="↗ Ofensivo", font=dict(color=ACCENT, size=10),
                 showarrow=False),
            dict(x=df_plot["Tiros a favor"].min(), y=avg_y - 5,
                 text="↘ Defensivo", font=dict(color=ACCENT, size=10),
                 showarrow=False),
        ],
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════
# RENDIMIENTO FÍSICO
# ══════════════════════════════════════════════════════════════════════════

def chart_distancia_por_jornada(df: pd.DataFrame, top_n: int = 15) -> go.Figure:
    """
    Barras horizontales APILADAS: distancia total por jornada para los Top N jugadores.
    Cada barra corresponde a una jornada del rango seleccionado en el filtro.
    """
    needed = {"Alias", "Jornada", "Distancia Total"}
    if not needed.issubset(df.columns):
        return _empty_fig("Columnas de distancia no disponibles")

    try:
        # Agregar por Alias+Jornada para evitar duplicados, convertir a km
        df_work = (
            df[["Alias", "Jornada", "Distancia Total"]]
            .dropna()
            .copy()
        )
        df_work["Distancia Total"] = pd.to_numeric(
            df_work["Distancia Total"], errors="coerce"
        ).fillna(0) / 1000.0

        # Pivot: filas=Alias, columnas=Jornada, valores=suma de distancia
        pivot = (
            df_work.groupby(["Alias", "Jornada"])["Distancia Total"]
            .sum()
            .unstack(fill_value=0.0)
        )

        # Top N jugadores por distancia total
        pivot["_total"] = pivot.sum(axis=1)
        pivot = pivot.nlargest(top_n, "_total").drop(columns="_total")
        pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=True).index]

        jornadas = sorted([int(c) for c in pivot.columns])

        palette = px.colors.sample_colorscale(
            "Teal", [i / max(len(jornadas) - 1, 1) for i in range(len(jornadas))]
        ) if len(jornadas) > 1 else [ACCENT]

        fig = go.Figure()
        for i, jornada in enumerate(jornadas):
            vals = [float(pivot.loc[p, jornada]) if jornada in pivot.columns else 0.0
                    for p in pivot.index]
            texts = [f"{v:.3f} km" if v > 0.0 else "" for v in vals]
            fig.add_trace(go.Bar(
                y=list(pivot.index),
                x=vals,
                name=f"Jornada {jornada}",
                orientation="h",
                marker_color=palette[i],
                text=texts,
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=9),
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    f"Jornada {jornada}: %{{x:.3f}} km<extra></extra>"
                ),
            ))

        layout = dict(**_LAYOUT)
        layout["margin"] = dict(l=10, r=10, t=70, b=10)
        fig.update_layout(
            **layout,
            barmode="stack",
            title=f"🏃 Distancia total por partido · Top {top_n} jugadores",
            xaxis_title="Distancia Total (km)",
            yaxis_title="",
            height=520,
            legend=dict(
                title="Jornada", bgcolor="rgba(0,0,0,0)",
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
        )
    except Exception as e:
        return _empty_fig(f"Error al generar gráfico de distancia: {e}")

    return fig


def chart_velocidad_maxima_jugadores(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Barras verticales AGRUPADAS: velocidad máxima por jornada para los Top N jugadores
    más rápidos. Etiqueta en la barra de mayor velocidad de cada jugador.
    """
    needed = {"Alias", "Jornada", "Velocidad Maxima Total"}
    if not needed.issubset(df.columns):
        return _empty_fig("Columna 'Velocidad Maxima Total' no disponible")

    try:
        df_work = (
            df[["Alias", "Jornada", "Velocidad Maxima Total"]]
            .dropna()
            .copy()
        )
        df_work["Velocidad Maxima Total"] = pd.to_numeric(
            df_work["Velocidad Maxima Total"], errors="coerce"
        ).fillna(0)

        # Pivot: filas=Alias, columnas=Jornada, valores=máximo de velocidad
        pivot = (
            df_work.groupby(["Alias", "Jornada"])["Velocidad Maxima Total"]
            .max()
            .unstack(fill_value=0.0)
        )

        # Top N jugadores por velocidad máxima
        pivot["_max"] = pivot.max(axis=1)
        pivot = pivot.nlargest(top_n, "_max")
        order = pivot["_max"].sort_values(ascending=False).index.tolist()
        pivot = pivot.drop(columns="_max").loc[order]

        # Máximo absoluto por jugador (para la etiqueta)
        max_vel = pivot.max(axis=1).to_dict()

        jornadas = sorted([int(c) for c in pivot.columns])

        palette = px.colors.sample_colorscale(
            "Teal", [i / max(len(jornadas) - 1, 1) for i in range(len(jornadas))]
        ) if len(jornadas) > 1 else [ACCENT]

        fig = go.Figure()
        for i, jornada in enumerate(jornadas):
            vals = [float(pivot.loc[p, jornada]) if jornada in pivot.columns else None
                    for p in order]
            texts = []
            for p, v in zip(order, vals):
                if v is not None and v > 0 and abs(v - float(max_vel.get(p, 0))) < 0.05:
                    texts.append(f"{v:.1f}")
                else:
                    texts.append("")
            fig.add_trace(go.Bar(
                x=order,
                y=vals,
                name=f"Jornada {jornada}",
                marker_color=palette[i],
                text=texts,
                textposition="outside",
                textfont=dict(size=9, color="#ccd6f6"),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"Jornada {jornada}: %{{y:.1f}} km/h<extra></extra>"
                ),
            ))

        vel_max_global = float(df_work["Velocidad Maxima Total"].max())
        media_vel = float(df_work["Velocidad Maxima Total"].mean())
        fig.add_hline(
            y=media_vel, line_dash="dot", line_color=RED,
            annotation_text=f"Media {media_vel:.1f} km/h",
            annotation_position="right",
            annotation_font=dict(color=RED, size=10),
        )

        layout = dict(**_LAYOUT)
        layout["margin"] = dict(l=10, r=10, t=70, b=10)
        fig.update_layout(
            **layout,
            barmode="group",
            title=f"⚡ Top {top_n} jugadores más rápidos · Velocidad máxima por jornada",
            xaxis_title="Jugador",
            yaxis_title="Velocidad Máxima (km/h)",
            height=460,
            legend=dict(
                title="Jornada", bgcolor="rgba(0,0,0,0)",
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
            yaxis=dict(range=[0, vel_max_global * 1.15]),
        )
    except Exception as e:
        return _empty_fig(f"Error al generar gráfico de velocidad: {e}")

    return fig


def chart_evolucion_jornada(df: pd.DataFrame, jugador: str) -> go.Figure:
    """
    Línea temporal: evolución de minutos jugados por jornada para un jugador.
    Acepta tanto un df completo (con columna Alias) como uno ya filtrado
    por jugador (solo columnas Jornada y Minutos jugados).
    """
    if "Jornada" not in df.columns or "Minutos jugados" not in df.columns:
        return _empty_fig("Columnas de jornada no disponibles")

    # Si el df ya viene filtrado por jugador (sin columna Alias), usarlo directo
    if "Alias" in df.columns:
        df_jug = df[df["Alias"] == jugador][["Jornada", "Minutos jugados"]].copy()
    else:
        df_jug = df[["Jornada", "Minutos jugados"]].copy()

    df_jug = df_jug.sort_values("Jornada")

    if df_jug.empty:
        return _empty_fig(f"No hay datos para {jugador}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_jug["Jornada"],
        y=df_jug["Minutos jugados"],
        mode="lines+markers",
        line=dict(color=ACCENT, width=2),
        marker=dict(size=7, color=ACCENT),
        fill="tozeroy",
        fillcolor="rgba(100,255,218,0.1)",
        name=jugador,
    ))

    # Línea de 90 min
    fig.add_hline(
        y=90, line_dash="dash", line_color=RED,
        annotation_text="90 min", annotation_position="right",
    )

    fig.update_layout(
        **_LAYOUT,
        title=f"📈 Evolución de minutos · {jugador}",
        xaxis_title="Jornada",
        yaxis_title="Minutos jugados",
        height=400,
    )
    return fig


def chart_equipo_radar(df: pd.DataFrame, equipo: str) -> go.Figure:
    """
    Radar chart: perfil estadístico de un equipo vs la media de LaLiga.
    Normaliza los valores al rango [0, 1] para comparación justa.
    """
    dims = {
        "Goles": "Goles a favor",
        "xG":    "xG (Sin Pen.) a favor",
        "Tiros": "Tiros a favor",
        "Posesión": "% posesión",
        "Presiones": "Presiones",
    }
    # Filtrar dimensiones disponibles
    dims = {k: v for k, v in dims.items() if v in df.columns}
    if len(dims) < 3:
        return _empty_fig("No hay suficientes métricas para el radar")

    df_num = df[list(dims.values())].copy()
    # Normalizar [0,1]
    df_norm = (df_num - df_num.min()) / (df_num.max() - df_num.min() + 1e-9)
    df_norm["Equipo"] = df["Equipo"].values

    row_equipo = df_norm[df_norm["Equipo"] == equipo]
    row_media  = df_norm.drop(columns=["Equipo"]).mean()

    if row_equipo.empty:
        return _empty_fig(f"Equipo '{equipo}' no encontrado")

    labels = list(dims.keys())
    vals_eq  = row_equipo[list(dims.values())].values[0].tolist()
    vals_med = row_media[list(dims.values())].tolist()

    fig = go.Figure()
    for vals, name, color in [
        (vals_eq,  equipo,        ACCENT),
        (vals_med, "Media LaLiga", "#8892b0"),
    ]:
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=labels + [labels[0]],
            fill="toself",
            fillcolor=color.replace("#", "rgba(") + ",0.15)" if color.startswith("#")
                      else color,
            line=dict(color=color, width=2),
            name=name,
        ))

    # Fix fillcolor properly
    fig.data[0].fillcolor = "rgba(100,255,218,0.15)"
    fig.data[1].fillcolor = "rgba(136,146,176,0.15)"

    fig.update_layout(
        **_LAYOUT,
        title=f"🕸️ Perfil estadístico · {equipo}",
        polar=dict(
            bgcolor="rgba(26,29,39,0.6)",
            radialaxis=dict(visible=True, range=[0, 1],
                            tickfont=dict(color="#8892b0")),
            angularaxis=dict(tickfont=dict(color="#ccd6f6")),
        ),
        height=460,
    )
    return fig


# ── Helper ────────────────────────────────────────────────────────────────

def _empty_fig(msg: str) -> go.Figure:
    """Devuelve una figura vacía con un mensaje de error."""
    fig = go.Figure()
    fig.add_annotation(
        text=f"⚠️ {msg}", xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=14, color="#8892b0"),
    )
    fig.update_layout(**_LAYOUT, height=300)
    return fig
