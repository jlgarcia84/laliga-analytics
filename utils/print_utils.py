"""
utils/print_utils.py — Botón de impresión de página
====================================================
Inyecta JavaScript (window.parent.print()) para imprimir la página
completa de Streamlit.  Se incluye también CSS @media print para
ocultar elementos de la interfaz durante la impresión.
"""

import streamlit as st
import streamlit.components.v1 as components


# ── CSS de impresión (inyectado en el layout principal) ───────────────────
PRINT_CSS = """
<style>
@media print {
    /* Ocultar sidebar, cabecera y elementos de navegación */
    [data-testid="stSidebar"]       { display: none !important; }
    [data-testid="stHeader"]        { display: none !important; }
    [data-testid="stToolbar"]       { display: none !important; }
    .stDeployButton                 { display: none !important; }
    footer                          { display: none !important; }

    /* Fondo blanco para impresión */
    .stApp, .block-container {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* Ajustar márgenes */
    .block-container {
        padding: 0.5rem 1rem !important;
        max-width: 100% !important;
    }

    /* Asegurar que las tablas y gráficos se impriman */
    .stDataFrame, .js-plotly-plot {
        break-inside: avoid;
        page-break-inside: avoid;
    }

    /* Ocultar botones de acción durante impresión */
    .stButton, .stDownloadButton { display: none !important; }
}
</style>
"""


def inject_print_css() -> None:
    """
    Inyecta el CSS de impresión en la página.
    Llamar una vez al inicio de cada página que soporte impresión.
    """
    st.markdown(PRINT_CSS, unsafe_allow_html=True)


def render_print_button(label: str = "🖨️ Imprimir página") -> None:
    """
    Renderiza un botón HTML que ejecuta window.parent.print().
    Compatible con el entorno iframe de Streamlit.
    """
    components.html(
        f"""
        <button
            onclick="window.parent.print()"
            title="Imprimir esta página"
            style="
                background: #2e3250;
                color: #ccd6f6;
                border: 1px solid #3d4f7c;
                border-radius: 8px;
                padding: 0.45rem 1.1rem;
                font-size: 0.85rem;
                font-family: Inter, sans-serif;
                cursor: pointer;
                transition: background 0.15s;
            "
            onmouseover="this.style.background='#3d4f7c'"
            onmouseout="this.style.background='#2e3250'"
        >
            {label}
        </button>
        """,
        height=48,
    )
