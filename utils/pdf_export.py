"""
utils/pdf_export.py — Exportación a PDF con ReportLab + Matplotlib
===================================================================
Genera un PDF profesional con:
  • Cabecera con título, fecha y usuario activo
  • Métricas clave
  • Gráficos estáticos (matplotlib)
  • Tabla de datos formateada (reportlab)
  • Pie de página con número de página

Devuelve bytes para usar directamente con st.download_button.
"""

import io
from datetime import datetime

import matplotlib
matplotlib.use("Agg")                    # backend no interactivo (sin pantalla)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable, KeepTogether,
)
from reportlab.lib.utils import ImageReader

# ── Paleta de colores para el PDF ─────────────────────────────────────────
C_PRIMARY  = colors.HexColor("#1e3a5f")
C_ACCENT   = colors.HexColor("#0d9488")
C_LIGHT    = colors.HexColor("#f0f9ff")
C_DARK     = colors.HexColor("#1e293b")
C_GRAY     = colors.HexColor("#64748b")
C_WHITE    = colors.white
C_BLACK    = colors.black
C_HEADER   = colors.HexColor("#0f172a")
C_ROW_ALT  = colors.HexColor("#f8fafc")

PAGE_W, PAGE_H = A4


# ── Estilos de párrafo ─────────────────────────────────────────────────────
def _build_styles():
    base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=20, textColor=C_PRIMARY,
            spaceAfter=4, alignment=TA_LEFT,
            fontName="Helvetica-Bold",
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontSize=10, textColor=C_GRAY,
            spaceAfter=12, alignment=TA_LEFT,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontSize=12, textColor=C_PRIMARY,
            spaceBefore=14, spaceAfter=6,
            fontName="Helvetica-Bold",
            borderPad=2,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=9, textColor=C_DARK,
            spaceAfter=4,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["Normal"],
            fontSize=8, textColor=C_GRAY,
            spaceAfter=8, alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "Footer",
            parent=base["Normal"],
            fontSize=7, textColor=C_GRAY,
            alignment=TA_CENTER,
        ),
    }
    return styles


# ── Función auxiliar: tabla reportlab desde DataFrame ─────────────────────
def _df_to_rl_table(df: pd.DataFrame, max_rows: int = 40) -> Table:
    """Convierte un DataFrame en una Table de ReportLab."""
    df_show = df.head(max_rows).copy()

    # Formatear números
    for col in df_show.select_dtypes(include="float").columns:
        df_show[col] = df_show[col].map(lambda x: f"{x:.2f}" if pd.notna(x) else "—")

    headers = list(df_show.columns)
    data = [headers] + df_show.astype(str).values.tolist()

    # Calcular anchos proporcionales
    col_count = len(headers)
    avail_w = PAGE_W - 2 * cm
    col_w = avail_w / col_count

    table = Table(data, colWidths=[col_w] * col_count, repeatRows=1)
    table.setStyle(TableStyle([
        # Cabecera
        ("BACKGROUND",    (0, 0), (-1, 0), C_HEADER),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING",    (0, 0), (-1, 0), 6),
        # Filas de datos
        ("FONTSIZE",      (0, 1), (-1, -1), 7),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("TEXTCOLOR",     (0, 1), (-1, -1), C_DARK),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
        ("TOPPADDING",    (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        # Bordes
        ("GRID",          (0, 0), (-1, -1), 0.3, C_GRAY),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, C_ACCENT),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


# ── Función auxiliar: gráfico matplotlib → buffer PNG ────────────────────
def _bar_chart_png(
    labels: list, values: list,
    title: str, xlabel: str = "",
    color: str = "#0d9488",
    figsize: tuple = (7, 3.5),
) -> io.BytesIO:
    """Genera un gráfico de barras horizontal y lo devuelve como PNG en memoria."""
    fig, ax = plt.subplots(figsize=figsize, facecolor="#f0f9ff")
    ax.set_facecolor("#f8fafc")

    bars = ax.barh(labels, values, color=color, edgecolor="#e2e8f0", height=0.6)

    # Etiquetas de valor
    for bar, val in zip(bars, values):
        ax.text(
            val + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}" if isinstance(val, float) else str(val),
            va="center", ha="left", fontsize=7, color="#1e293b",
        )

    ax.set_title(title, fontsize=10, fontweight="bold", color="#1e3a5f", pad=8)
    ax.set_xlabel(xlabel, fontsize=8, color="#64748b")
    ax.tick_params(axis="both", labelsize=7, colors="#1e293b")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#cbd5e1")
    ax.grid(axis="x", linestyle="--", alpha=0.4, color="#cbd5e1")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _scatter_chart_png(
    x: list, y: list, labels: list,
    title: str, xlabel: str = "", ylabel: str = "",
    figsize: tuple = (7, 3.5),
) -> io.BytesIO:
    """Genera un scatter plot y lo devuelve como PNG en memoria."""
    fig, ax = plt.subplots(figsize=figsize, facecolor="#f0f9ff")
    ax.set_facecolor("#f8fafc")

    ax.scatter(x, y, color="#0d9488", s=70, edgecolors="#e2e8f0", zorder=3)

    # Línea diagonal xG = Goles
    max_val = max(max(x), max(y)) + 2
    ax.plot([0, max_val], [0, max_val], linestyle="--", color="#94a3b8",
            linewidth=0.8, label="xG = Goles")

    # Etiquetas de equipos (abreviadas)
    for xi, yi, lbl in zip(x, y, labels):
        ax.annotate(
            str(lbl).split()[-1][:8], (xi, yi),
            xytext=(3, 3), textcoords="offset points",
            fontsize=6, color="#334155",
        )

    ax.set_title(title, fontsize=10, fontweight="bold", color="#1e3a5f", pad=8)
    ax.set_xlabel(xlabel, fontsize=8, color="#64748b")
    ax.set_ylabel(ylabel, fontsize=8, color="#64748b")
    ax.tick_params(labelsize=7, colors="#1e293b")
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#cbd5e1")
    ax.legend(fontsize=7)
    ax.grid(linestyle="--", alpha=0.3, color="#cbd5e1")
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


# ── Callback para pie de página ───────────────────────────────────────────
class _PageNumCanvas:
    """Dibuja pie de página con número de página en cada hoja."""
    def __init__(self, app_name: str, usuario: str):
        self.app_name = app_name
        self.usuario  = usuario

    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_GRAY)
        footer_text = (
            f"{self.app_name}  ·  Usuario: {self.usuario}  ·  "
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}  ·  "
            f"Página {doc.page}"
        )
        canvas.drawCentredString(PAGE_W / 2, 1.2 * cm, footer_text)
        canvas.setStrokeColor(C_ACCENT)
        canvas.setLineWidth(0.5)
        canvas.line(1.5 * cm, 1.5 * cm, PAGE_W - 1.5 * cm, 1.5 * cm)
        canvas.restoreState()


# ══════════════════════════════════════════════════════════════════════════
# GENERADORES PÚBLICOS
# ══════════════════════════════════════════════════════════════════════════

def generate_pdf_estadisticas(
    df: pd.DataFrame,
    equipo_sel: str,
    usuario: str = "analista",
) -> bytes:
    """
    Genera el PDF de la página de Estadísticas de Equipos.

    Parámetros
    ----------
    df         : DataFrame con los datos de equipos (puede estar filtrado)
    equipo_sel : Nombre del equipo seleccionado o "Todos"
    usuario    : Nombre del usuario activo (para el pie de página)

    Retorna
    -------
    bytes del PDF generado en memoria.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=2 * cm,
    )
    styles = _build_styles()
    story  = []

    # ── Cabecera ─────────────────────────────────────────────────────────
    story.append(Paragraph("⚽ LaLiga Analytics", styles["title"]))
    story.append(Paragraph(
        f"Estadísticas de Equipos · Temporada 2024/25 · "
        f"Filtro: <b>{equipo_sel}</b> · "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=C_ACCENT, spaceAfter=10))

    # ── Métricas rápidas ─────────────────────────────────────────────────
    story.append(Paragraph("Resumen", styles["section"]))
    avg_gf = df["Goles a favor"].mean() if "Goles a favor" in df.columns else 0
    avg_gc = df["Goles en contra"].mean() if "Goles en contra" in df.columns else 0

    metrics_data = [
        ["Equipos analizados", "Media goles a favor", "Media goles en contra"],
        [str(len(df)), f"{avg_gf:.1f}", f"{avg_gc:.1f}"],
    ]
    metrics_table = Table(metrics_data, colWidths=[PAGE_W / 3 - 2 * cm] * 3)
    metrics_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_LIGHT),
        ("BACKGROUND",    (0, 1), (-1, 1), C_WHITE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_GRAY),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 16),
        ("TEXTCOLOR",     (0, 1), (-1, 1), C_PRIMARY),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1, C_ACCENT),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 12))

    # ── Gráfico 1: Goles a favor ──────────────────────────────────────────
    if "Goles a favor" in df.columns and "Equipo" in df.columns:
        story.append(Paragraph("Goles a favor por equipo", styles["section"]))
        df_sorted = df.sort_values("Goles a favor", ascending=True)
        img_buf = _bar_chart_png(
            labels=df_sorted["Equipo"].tolist(),
            values=df_sorted["Goles a favor"].tolist(),
            title="Goles a favor · LaLiga 2024/25",
            xlabel="Goles",
        )
        story.append(RLImage(img_buf, width=16 * cm, height=8 * cm))
        story.append(Paragraph(
            "Fuente: StatsBomb · Base de datos SQLite local",
            styles["caption"],
        ))
        story.append(Spacer(1, 8))

    # ── Gráfico 2: xG vs Goles ────────────────────────────────────────────
    if {"xG (Sin Pen.) a favor", "Goles a favor", "Equipo"}.issubset(df.columns):
        story.append(Paragraph(
            "xG esperados vs Goles reales", styles["section"]
        ))
        img_buf2 = _scatter_chart_png(
            x=df["xG (Sin Pen.) a favor"].tolist(),
            y=df["Goles a favor"].tolist(),
            labels=df["Equipo"].tolist(),
            title="xG vs Goles · Sobrerendimiento / Infrarendimiento",
            xlabel="xG (Sin Pen.) a favor",
            ylabel="Goles a favor",
        )
        story.append(RLImage(img_buf2, width=16 * cm, height=7.5 * cm))
        story.append(Paragraph(
            "Los equipos sobre la diagonal convierten más de lo esperado por xG.",
            styles["caption"],
        ))
        story.append(Spacer(1, 8))

    # ── Tabla de datos ────────────────────────────────────────────────────
    story.append(Paragraph("Tabla de datos", styles["section"]))
    cols_pdf = ["Equipo", "Partidos", "Goles a favor", "Goles en contra",
                "xG (Sin Pen.) a favor", "% posesión", "Tiros a favor"]
    cols_pdf = [c for c in cols_pdf if c in df.columns]
    story.append(_df_to_rl_table(df[cols_pdf], max_rows=25))
    story.append(Paragraph(
        f"Mostrando {min(25, len(df))} de {len(df)} equipos",
        styles["caption"],
    ))

    # ── Build ─────────────────────────────────────────────────────────────
    cb = _PageNumCanvas("LaLiga Analytics", usuario)
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    return buf.getvalue()


def generate_pdf_fisico(
    df: pd.DataFrame,
    equipo_sel: str,
    jugador_sel: str,
    usuario: str = "analista",
) -> bytes:
    """
    Genera el PDF de la página de Rendimiento Físico.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=2 * cm,
    )
    styles = _build_styles()
    story  = []

    # ── Cabecera ─────────────────────────────────────────────────────────
    story.append(Paragraph("⚽ LaLiga Analytics", styles["title"]))
    filtro_str = (
        f"Equipo: <b>{equipo_sel}</b> · Jugador: <b>{jugador_sel}</b>"
        if jugador_sel != "Todos"
        else f"Equipo: <b>{equipo_sel}</b>"
    )
    story.append(Paragraph(
        f"Rendimiento Físico · Temporada 2024/25 · {filtro_str} · "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=C_ACCENT, spaceAfter=10))

    # ── Métricas ──────────────────────────────────────────────────────────
    story.append(Paragraph("Resumen", styles["section"]))
    avg_min = df["Minutos jugados"].mean() if "Minutos jugados" in df.columns else 0
    max_min = df["Minutos jugados"].max() if "Minutos jugados" in df.columns else 0

    metrics_data = [
        ["Registros", "Media minutos", "Máx. minutos"],
        [f"{len(df):,}", f"{avg_min:.1f}", f"{max_min:.0f}"],
    ]
    m_table = Table(metrics_data, colWidths=[PAGE_W / 3 - 2 * cm] * 3)
    m_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), C_LIGHT),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("FONTNAME",      (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 1), (-1, 1), 16),
        ("TEXTCOLOR",     (0, 1), (-1, 1), C_PRIMARY),
        ("TEXTCOLOR",     (0, 0), (-1, 0), C_GRAY),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1, C_ACCENT),
    ]))
    story.append(m_table)
    story.append(Spacer(1, 12))

    # ── Gráfico: Top 15 jugadores por minutos ─────────────────────────────
    if {"Alias", "Minutos jugados"}.issubset(df.columns):
        story.append(Paragraph("Top 15 jugadores por minutos jugados", styles["section"]))
        top = (
            df.groupby("Alias")["Minutos jugados"]
            .sum().nlargest(15).reset_index()
            .sort_values("Minutos jugados", ascending=True)
        )
        img_buf = _bar_chart_png(
            labels=top["Alias"].tolist(),
            values=top["Minutos jugados"].tolist(),
            title="Top 15 jugadores · Minutos totales",
            xlabel="Minutos jugados",
        )
        story.append(RLImage(img_buf, width=16 * cm, height=8 * cm))
        story.append(Paragraph(
            "Fuente: LaLiga Rendimiento 2024/25 · Base de datos SQLite local",
            styles["caption"],
        ))
        story.append(Spacer(1, 8))

    # ── Tabla de datos ────────────────────────────────────────────────────
    story.append(Paragraph("Tabla de datos", styles["section"]))
    cols_pdf = ["Jornada", "Equipo", "Alias", "Demarcacion", "Minutos jugados"]
    cols_pdf = [c for c in cols_pdf if c in df.columns]
    story.append(_df_to_rl_table(df[cols_pdf], max_rows=40))
    story.append(Paragraph(
        f"Mostrando {min(40, len(df)):,} de {len(df):,} registros",
        styles["caption"],
    ))

    cb = _PageNumCanvas("LaLiga Analytics", usuario)
    doc.build(story, onFirstPage=cb, onLaterPages=cb)
    return buf.getvalue()
