"""
data/database.py — Fuente de datos 1: Base de datos SQLite
=============================================================
Gestiona la conexión a una base de datos SQLite local que se crea
automáticamente a partir de los ficheros Excel la primera vez que
se usa la aplicación.

Tablas creadas:
  • equipos_stats      — estadísticas avanzadas por equipo (StatsBomb)
  • rendimiento_fisico — datos físicos por jugador (hoja "Físico")

Uso del caché:
  • @st.cache_data  → cachea los DataFrames resultantes de cada consulta.
    Cada función tiene un TTL distinto según la volatilidad del dato.
"""

import os
import sqlite3
import pandas as pd
import streamlit as st

# ── Rutas absolutas ────────────────────────────────────────────────────────
# _APP_DIR apunta a la carpeta que contiene app.py:
#   · Local:           …/Tarea 8/app/
#   · Streamlit Cloud: /mount/src/   (raíz del repositorio)
_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # app/

DB_PATH      = os.path.join(_APP_DIR, "laliga.db")
EXCEL_STATS  = os.path.join(_APP_DIR, "TeamStats1a_Statsbomb_24_25.xlsx")
# El xlsm original pesa >100 MB (límite GitHub). Se usa el CSV pre-exportado.
CSV_FISICO   = os.path.join(_APP_DIR, "LaLigaRendimiento_Fisico.csv")


# ── Inicialización de la base de datos ────────────────────────────────────

def init_database() -> bool:
    """
    Crea la base de datos SQLite e importa los datos si aún no existe
    O si las tablas están vacías (puede ocurrir si el primer deploy falló
    porque los ficheros de datos aún no estaban en el repositorio).

    Retorna True si la BD ya tenía datos, False si se acaba de crear.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Comprobar si las tablas existen Y tienen datos suficientes
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='rendimiento_fisico'"
    )
    table_exists = cursor.fetchone() is not None

    row_count = 0
    if table_exists:
        cursor.execute("SELECT COUNT(*) FROM rendimiento_fisico")
        row_count = cursor.fetchone()[0]

    # Recrear si no existe o si está vacía/incompleta (< 100 filas)
    needs_create = not table_exists or row_count < 100

    if needs_create:
        _create_tables(conn)

    conn.close()
    return not needs_create


def _create_tables(conn: sqlite3.Connection) -> None:
    """Importa los ficheros de datos y crea/recrea las tablas en la BD."""

    with st.spinner("⏳ Creando base de datos SQLite desde los ficheros de datos…"):

        # ── Tabla equipos_stats ──────────────────────────────────────────
        try:
            df_stats = pd.read_excel(EXCEL_STATS)
            # Limpiar columnas sin nombre
            df_stats = df_stats.loc[:, ~df_stats.columns.str.startswith("Unnamed")]
            df_stats.to_sql("equipos_stats", conn, if_exists="replace", index=False)
        except FileNotFoundError:
            st.error(f"No se encontró: {EXCEL_STATS}")

        # ── Tabla rendimiento_fisico (CSV pre-exportado desde la hoja "Físico") ──
        try:
            df_fisico = pd.read_csv(CSV_FISICO, encoding="utf-8-sig", nrows=10_000)
            df_fisico.to_sql("rendimiento_fisico", conn, if_exists="replace", index=False)
        except FileNotFoundError:
            st.error(f"No se encontró: {CSV_FISICO}")

    conn.commit()
    st.success("✅ Base de datos creada correctamente.")


# ── Funciones de consulta ─────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def query_equipos_stats(equipo: str | None = None) -> pd.DataFrame:
    """
    Consulta la tabla equipos_stats.
    Si se indica equipo, filtra por él.
    Resultado cacheado 5 minutos.
    """
    init_database()
    conn = sqlite3.connect(DB_PATH)

    if equipo and equipo != "Todos":
        sql = "SELECT * FROM equipos_stats WHERE Equipo = ?"
        df = pd.read_sql_query(sql, conn, params=(equipo,))
    else:
        sql = "SELECT * FROM equipos_stats ORDER BY Equipo"
        df = pd.read_sql_query(sql, conn)

    conn.close()
    return df


@st.cache_data(ttl=300, show_spinner=False)
def query_rendimiento(
    equipo: str | None = None,
    jugador: str | None = None,
    limite: int = 500,
) -> pd.DataFrame:
    """
    Consulta la tabla rendimiento_fisico con filtros opcionales.
    Resultado cacheado 5 minutos.
    """
    init_database()
    conn = sqlite3.connect(DB_PATH)

    conditions = []
    params: list = []

    if equipo and equipo != "Todos":
        conditions.append("Equipo = ?")
        params.append(equipo)
    if jugador and jugador != "Todos":
        conditions.append("Alias = ?")
        params.append(jugador)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM rendimiento_fisico {where} LIMIT {limite}"

    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


@st.cache_data(ttl=600, show_spinner=False)
def get_equipos_lista() -> list[str]:
    """Devuelve la lista de equipos únicos de la tabla equipos_stats."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT DISTINCT Equipo FROM equipos_stats ORDER BY Equipo", conn)
    conn.close()
    return df["Equipo"].tolist()


@st.cache_data(ttl=600, show_spinner=False)
def get_equipos_fisico_lista() -> list[str]:
    """Devuelve la lista de equipos únicos de la tabla rendimiento_fisico.
    Se usa en la página Físico para que los nombres coincidan exactamente."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT DISTINCT Equipo FROM rendimiento_fisico ORDER BY Equipo", conn
    )
    conn.close()
    return df["Equipo"].dropna().tolist()


def query_evolucion_jugador(jugador: str) -> pd.DataFrame:
    """Devuelve TODAS las jornadas de un jugador leyendo directamente del CSV.
    Sin caché para garantizar siempre datos frescos y completos."""
    try:
        df = pd.read_csv(
            CSV_FISICO,
            encoding="utf-8-sig",
            usecols=["Alias", "Jornada", "Minutos jugados"],
        )
        return (
            df[df["Alias"] == jugador][["Jornada", "Minutos jugados"]]
            .sort_values("Jornada")
            .reset_index(drop=True)
        )
    except Exception:
        return pd.DataFrame(columns=["Jornada", "Minutos jugados"])


@st.cache_data(ttl=600, show_spinner=False)
def get_jugadores_lista(equipo: str | None = None) -> list[str]:
    """Devuelve la lista de jugadores (Alias) únicos, opcionalmente por equipo."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    if equipo and equipo != "Todos":
        df = pd.read_sql_query(
            "SELECT DISTINCT Alias FROM rendimiento_fisico WHERE Equipo = ? ORDER BY Alias",
            conn, params=(equipo,)
        )
    else:
        df = pd.read_sql_query(
            "SELECT DISTINCT Alias FROM rendimiento_fisico ORDER BY Alias LIMIT 200", conn
        )
    conn.close()
    return df["Alias"].dropna().tolist()


@st.cache_data(ttl=300, show_spinner=False)
def get_db_info() -> dict:
    """Devuelve información básica sobre las tablas de la BD."""
    init_database()
    conn = sqlite3.connect(DB_PATH)
    info = {}
    for table in ("equipos_stats", "rendimiento_fisico"):
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        rows = cursor.fetchone()[0]
        cursor.execute(f"PRAGMA table_info({table})")
        cols = len(cursor.fetchall())
        info[table] = {"filas": rows, "columnas": cols}
    conn.close()
    return info
