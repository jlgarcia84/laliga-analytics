"""
data/api_client.py — Fuente de datos 2: API externa (football-data.org)
========================================================================
Conecta con la API pública de football-data.org para obtener datos en
tiempo real de LaLiga (clasificación, partidos recientes y próximos).

Registro gratuito en: https://www.football-data.org/client/register
→ El plan gratuito permite 10 peticiones/minuto.

Caché:
  • @st.cache_data(ttl=3600) — resultados válidos durante 1 hora para no
    consumir el límite gratuito de la API en cada interacción.
"""

import requests
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

# ── Configuración de la API ───────────────────────────────────────────────
API_BASE    = "https://api.football-data.org/v4"
COMPETITION = "PD"          # LaLiga · Primera División
TIMEOUT     = 8             # segundos de timeout por petición


def get_api_key() -> str | None:
    """
    Obtiene la API key por orden de prioridad:
      1. st.secrets["FOOTBALL_API_KEY"]   (fichero .streamlit/secrets.toml)
      2. st.session_state["api_key"]      (introducida por el usuario en la UI)
    """
    # 1. Desde secrets.toml
    try:
        key = st.secrets.get("FOOTBALL_API_KEY", "")
        if key:
            return key
    except Exception:
        pass

    # 2. Desde session_state (introducida manualmente en la UI)
    return st.session_state.get("api_key", None) or None


def _headers(api_key: str) -> dict:
    return {"X-Auth-Token": api_key}


def render_api_key_input() -> str | None:
    """
    Muestra un widget para introducir la API key si no está configurada.
    Devuelve la key si está disponible, None si no.
    """
    key = get_api_key()
    if key:
        st.success(f"🔑 API key configurada ({key[:6]}…)")
        return key

    st.info(
        "🔑 **API key de football-data.org no configurada.**\n\n"
        "Regístrate gratis en [football-data.org](https://www.football-data.org/client/register) "
        "y obtén tu API key. Luego:\n\n"
        "**Opción A (recomendada):** Añade en `.streamlit/secrets.toml`:\n"
        "```toml\nFOOTBALL_API_KEY = \"tu_api_key\"\n```\n\n"
        "**Opción B (temporal):** Introdúcela aquí:"
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        key_input = st.text_input(
            "API Key",
            type="password",
            placeholder="Pega tu API key aquí…",
            label_visibility="collapsed",
        )
    with col2:
        if st.button("✅ Guardar", use_container_width=True):
            if key_input.strip():
                st.session_state["api_key"] = key_input.strip()
                st.rerun()
            else:
                st.error("La key no puede estar vacía.")

    return None


# ── Endpoints ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_standings(api_key: str) -> pd.DataFrame | None:
    """
    GET /v4/competitions/PD/standings
    Devuelve la clasificación de LaLiga como DataFrame.
    Resultado cacheado 1 hora.
    """
    url = f"{API_BASE}/competitions/{COMPETITION}/standings"
    try:
        resp = requests.get(url, headers=_headers(api_key), timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Error HTTP {resp.status_code}: {resp.json().get('message', str(e))}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

    data = resp.json()
    table = data["standings"][0]["table"]  # TOTAL standings

    rows = []
    for entry in table:
        rows.append({
            "Pos":    entry["position"],
            "Equipo": entry["team"]["name"],
            "PJ":     entry["playedGames"],
            "G":      entry["won"],
            "E":      entry["draw"],
            "P":      entry["lost"],
            "GF":     entry["goalsFor"],
            "GC":     entry["goalsAgainst"],
            "DG":     entry["goalDifference"],
            "Pts":    entry["points"],
        })

    return pd.DataFrame(rows)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_matches(api_key: str, status: str = "FINISHED") -> pd.DataFrame | None:
    """
    GET /v4/competitions/PD/matches?status=FINISHED|SCHEDULED
    Devuelve los partidos recientes o próximos como DataFrame.
    Resultado cacheado 1 hora.
    """
    url = f"{API_BASE}/competitions/{COMPETITION}/matches"
    params = {"status": status, "limit": 15}
    try:
        resp = requests.get(
            url, headers=_headers(api_key), params=params, timeout=TIMEOUT
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Error HTTP {resp.status_code}: {resp.json().get('message', str(e))}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

    matches = resp.json().get("matches", [])
    if not matches:
        return pd.DataFrame()

    rows = []
    for m in matches:
        fecha_raw = m.get("utcDate", "")
        try:
            fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
            fecha_str = fecha.strftime("%d/%m/%Y %H:%M")
        except Exception:
            fecha_str = fecha_raw

        score = m.get("score", {}).get("fullTime", {})
        home_goals = score.get("home")
        away_goals = score.get("away")

        if home_goals is not None and away_goals is not None:
            resultado = f"{home_goals} - {away_goals}"
        else:
            resultado = "—"

        rows.append({
            "Fecha":    fecha_str,
            "Jornada":  m.get("matchday", ""),
            "Local":    m["homeTeam"]["name"],
            "Resultado": resultado,
            "Visitante": m["awayTeam"]["name"],
            "Estado":   m.get("status", ""),
        })

    # Ordenar: los más recientes primero
    df = pd.DataFrame(rows)
    if not df.empty and status == "FINISHED":
        df = df.sort_values("Fecha", ascending=False).reset_index(drop=True)

    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_team_list(api_key: str) -> pd.DataFrame | None:
    """
    GET /v4/competitions/PD/teams
    Devuelve el listado oficial de equipos de LaLiga con info básica.
    """
    url = f"{API_BASE}/competitions/{COMPETITION}/teams"
    try:
        resp = requests.get(url, headers=_headers(api_key), timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

    teams = resp.json().get("teams", [])
    rows = [
        {
            "Nombre":   t["name"],
            "Alias":    t.get("shortName", ""),
            "Fundación": t.get("founded", ""),
            "Estadio":  t.get("venue", ""),
            "Web":      t.get("website", ""),
        }
        for t in teams
    ]
    return pd.DataFrame(rows)
