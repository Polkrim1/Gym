import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.graph_objects as go

# ─────────────────────────────────────────
#  CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────
st.set_page_config(page_title="Gym Pro", page_icon="💪", layout="centered")

# ─────────────────────────────────────────
#  JSONBIN  (secrets: jsonbin_api_key, jsonbin_bin_id)
# ─────────────────────────────────────────
API_KEY = st.secrets["jsonbin_api_key"]
BIN_ID  = st.secrets["jsonbin_bin_id"]
URL     = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

# ─────────────────────────────────────────
#  EJERCICIOS POR CATEGORÍA
# ─────────────────────────────────────────
CATEGORIAS = {
    "🦵 Pierna"   : ["Sentadilla", "Sentadilla Búlgara", "Leg Press", "Extensión de Cuádriceps",
                     "Curl de Femorales", "Hip Thrust", "Peso Muerto Rumano", "Elevación de Gemelos",
                     "Zancadas", "Hack Squat"],
    "💪 Empuje"   : ["Press Banca", "Press Banca Inclinado", "Press Banca Declinado", "Aperturas con Mancuernas",
                     "Press Militar", "Press Arnold", "Elevaciones Laterales", "Elevaciones Frontales",
                     "Fondos en Paralelas", "Extensión de Tríceps", "Press Francés", "Patada de Tríceps"],
    "🏋️ Jalón"   : ["Peso Muerto", "Dominadas", "Jalón al Pecho", "Remo con Barra",
                     "Remo con Mancuerna", "Remo en Polea", "Face Pull", "Pull-over",
                     "Curl de Bíceps", "Curl Martillo", "Curl en Banco Scott", "Encogimientos de Hombros"],
    "🔥 Core"     : ["Plancha", "Crunch", "Russian Twist", "Rueda Abdominal",
                     "Elevación de Piernas", "Dead Bug", "Bird Dog", "Pallof Press"],
    "🏃 Cardio"   : ["Caminata (min)", "Carrera (min)", "Bicicleta (min)", "Elíptica (min)",
                     "Remo (min)", "Saltar la Cuerda (min)", "HIIT (min)"],
}

# ─────────────────────────────────────────
#  HELPERS DE FECHA EN ESPAÑOL
# ─────────────────────────────────────────
_DIAS  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
_MESES = ["","enero","febrero","marzo","abril","mayo","junio",
          "julio","agosto","septiembre","octubre","noviembre","diciembre"]

def fecha_es(d):
    return f"{_DIAS[d.weekday()]}, {d.day} de {_MESES[d.month]} {d.year}"

# ─────────────────────────────────────────
#  BASE DE DATOS (JSONBin)
# ─────────────────────────────────────────
def get_data() -> pd.DataFrame:
    """Lee todos los registros y normaliza columnas."""
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        data = r.json()
        if "record" in data and data["record"]:
            df = pd.DataFrame(data["record"])
            if df.empty:
                raise ValueError
            df["fecha"] = pd.to_datetime(df["fecha"]).dt.date
            df["peso"]  = pd.to_numeric(df["peso"],  errors="coerce").fillna(0)
            df["reps"]  = pd.to_numeric(df["reps"],  errors="coerce").fillna(0).astype(int)
            if "serie" not in df.columns:
                df["serie"] = 1
            if "row_id" not in df.columns:
                df["row_id"] = range(len(df))
            df["row_id"] = df["row_id"].astype(int)
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["row_id","fecha","ejercicio","peso","reps","serie"])


def _save(df: pd.DataFrame):
    """Serializa y guarda (convierte fechas a string)."""
    records = df.copy()
    records["fecha"] = records["fecha"].astype(str)
    requests.put(URL, json=records.to_dict(orient="records"), headers=HEADERS, timeout=10)


def add_serie(fecha, ejercicio, peso, reps):
    df = get_data()
    mask = (df["fecha"] == fecha) & (df["ejercicio"] == ejercicio)
    serie_num = int(df[mask]["serie"].max() + 1) if mask.any() else 1
    next_id   = int(df["row_id"].max() + 1) if not df.empty else 0

    nueva = pd.DataFrame({
        "row_id"   : [next_id],
        "fecha"    : [fecha],
        "ejercicio": [ejercicio],
        "peso"     : [peso],
        "reps"     : [reps],
        "serie"    : [serie_num],
    })
    df = pd.concat([df, nueva], ignore_index=True)
    _save(df)


def delete_by_id(row_id: int):
    df = get_data()
    _save(df[df["row_id"] != row_id])


def delete_day(fecha):
    df = get_data()
    _save(df[df["fecha"] != fecha])


# ─────────────────────────────────────────
#  CÁLCULOS
# ─────────────────────────────────────────
def e1rm(peso, reps):
    """Fórmula de Epley: 1RM estimado."""
    return round(peso * (1 + reps / 30), 1) if reps > 1 else float(peso)


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas calculadas."""
    df = df.copy()
    df["e1rm"]   = df.apply(lambda r: e1rm(r["peso"], r["reps"]), axis=1)
    df["volumen"] = df["peso"] * df["reps"]
    return df


# ─────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

      html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Poppins', sans-serif !important;
        background-color: #0D0D0D;
        color: #EEEEEE;
      }
      header, [data-testid="stToolbar"], footer { display: none !important; }

      /* Tabs */
      .stTabs [data-baseweb="tab-list"] {
        background: #1A1A1A; border-radius: 14px; padding: 4px; gap: 4px;
      }
      .stTabs [data-baseweb="tab"] {
        border-radius: 10px; font-weight: 600; color: #888; padding: 8px 14px;
      }
      .stTabs [aria-selected="true"] { background: #FF3D00 !important; color: #fff !important; }

      /* Cards */
      .pr-card {
        background: linear-gradient(135deg,#1A1A1A,#202020);
        border-radius: 16px; padding: 16px 20px; margin-bottom: 10px;
        border: 1px solid #2A2A2A; transition: border-color .2s;
      }
      .pr-card:hover { border-color: #FF3D00; }

      .serie-row {
        background: #1E1E1E; border-radius: 10px; padding: 10px 14px;
        margin-bottom: 6px; border-left: 3px solid #FF3D00;
        display: flex; justify-content: space-between; align-items: center;
      }

      /* Title gradient */
      h1 {
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(135deg,#FF3D00,#FF8C00);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
      }

      /* Métricas */
      [data-testid="stMetricValue"] { font-size: 1.4rem !important; color: #FF3D00; }

      /* Botón primario */
      .stButton > button {
        background: #FF3D00; color: #fff; border: none;
        border-radius: 10px; font-weight: 600; transition: background .2s;
      }
      .stButton > button:hover { background: #FF6130; }

      /* Expander */
      [data-testid="stExpander"] { border: 1px solid #2A2A2A; border-radius: 12px; }

      /* Inputs */
      .stSelectbox > div > div, .stNumberInput > div > div { border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────
def main():
    inject_css()
    st.markdown("# 💪 GYM PRO")
    st.markdown("<p style='color:#888;margin-top:-10px;'>Tu diario de entrenamiento</p>",
                unsafe_allow_html=True)

    if "fecha_sel" not in st.session_state:
        st.session_state.fecha_sel = datetime.date.today()

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Registro", "📊 Progreso", "🏆 Récords", "📋 Historial"])

    # ══════════════════════════════════════
    #  TAB 1 — REGISTRO
    # ══════════════════════════════════════
    with tab1:
        # — Selector de fecha —
        st.markdown("### 📅 Fecha")
        c1, c2, c3 = st.columns([1, 1, 2])
        if c1.button("Hoy",  use_container_width=True):
            st.session_state.fecha_sel = datetime.date.today()
        if c2.button("Ayer", use_container_width=True):
            st.session_state.fecha_sel = datetime.date.today() - datetime.timedelta(days=1)
        nueva = c3.date_input("Otra", value=st.session_state.fecha_sel, label_visibility="collapsed")
        if nueva != st.session_state.fecha_sel:
            st.session_state.fecha_sel = nueva

        st.markdown(f"**{fecha_es(st.session_state.fecha_sel)}**")
        st.markdown("---")

        # — Formulario: agregar serie —
        with st.expander("➕ Agregar Serie", expanded=True):
            cats = list(CATEGORIAS.keys()) + ["⚙️ Personalizado"]
            cat  = st.selectbox("Categoría", cats, key="cat_sel")

            if cat == "⚙️ Personalizado":
                ejercicio = st.text_input("Nombre del ejercicio", placeholder="ej. Sentadilla Sumo...")
            else:
                ejercicio = st.selectbox("Ejercicio", CATEGORIAS[cat], key="ej_sel")

            col_p, col_r = st.columns(2)
            peso = col_p.number_input("Peso (kg)", min_value=0.0, step=2.5, value=60.0)
            reps = col_r.number_input("Reps", min_value=1, max_value=200, step=1, value=10)

            # Preview en tiempo real
            est = e1rm(peso, reps)
            vol = peso * reps
            m1, m2 = st.columns(2)
            m1.metric("1RM estimado", f"{est} kg")
            m2.metric("Volumen",      f"{vol:.0f} kg")

            if st.button("💾 Guardar Serie", use_container_width=True):
                if ejercicio and ejercicio.strip():
                    add_serie(st.session_state.fecha_sel, ejercicio.strip(), peso, reps)
                    st.success("¡Serie guardada! 🔥")
                    st.rerun()
                else:
                    st.error("Escribe el nombre del ejercicio.")

        # — Registro del día —
        df = get_data()
        if not df.empty:
            dia = enrich(df[df["fecha"] == st.session_state.fecha_sel].copy())
            if not dia.empty:
                vol_total = dia["volumen"].sum()
                s1, s2, s3 = st.columns(3)
                s1.metric("Series",        len(dia))
                s2.metric("Ejercicios",    dia["ejercicio"].nunique())
                s3.metric("Volumen Total", f"{vol_total:.0f} kg")

                st.markdown("### Series del día")
                for ej in dia["ejercicio"].unique():
                    ej_data = dia[dia["ejercicio"] == ej]
                    vol_ej  = ej_data["volumen"].sum()
                    st.markdown(f"**{ej}** — Volumen: {vol_ej:.0f} kg")

                    for _, row in ej_data.iterrows():
                        colA, colB = st.columns([7, 1])
                        colA.markdown(
                            f'<div class="serie-row">'
                            f'<span>Serie {int(row["serie"])} &nbsp; '
                            f'<b>{row["peso"]} kg × {int(row["reps"])} reps</b></span>'
                            f'<span style="color:#888;font-size:.8rem">1RM: {row["e1rm"]} kg</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if colB.button("🗑️", key=f"del_{row['row_id']}"):
                            delete_by_id(int(row["row_id"]))
                            st.rerun()

                st.markdown("---")
                if st.button("🗑️ Borrar todo el día", use_container_width=True):
                    delete_day(st.session_state.fecha_sel)
                    st.success("Día eliminado.")
                    st.rerun()
            else:
                st.info("💤 Sin registros para este día. ¡A entrenar!")
        else:
            st.info("💤 No hay datos aún. ¡Empieza tu primer entrenamiento!")

    # ══════════════════════════════════════
    #  TAB 2 — PROGRESO
    # ══════════════════════════════════════
    with tab2:
        df = get_data()
        if df.empty or df["ejercicio"].nunique() == 0:
            st.info("Sin datos suficientes para mostrar progreso.")
        else:
            df = enrich(df)

            st.markdown("### 📊 Progreso por ejercicio")
            ej_sel = st.selectbox("Ejercicio", sorted(df["ejercicio"].unique()), key="prog_ej")

            metrica = st.radio(
                "Métrica",
                ["Peso máximo", "1RM estimado", "Volumen total"],
                horizontal=True,
            )

            df_ej = df[df["ejercicio"] == ej_sel].copy()
            df_ej["fecha_dt"] = pd.to_datetime(df_ej["fecha"])

            if metrica == "Peso máximo":
                daily   = df_ej.groupby("fecha_dt")["peso"].max().reset_index()
                y_col   = "peso"
                y_label = "Peso (kg)"
            elif metrica == "1RM estimado":
                daily   = df_ej.groupby("fecha_dt")["e1rm"].max().reset_index()
                y_col   = "e1rm"
                y_label = "1RM estimado (kg)"
            else:
                daily   = df_ej.groupby("fecha_dt")["volumen"].sum().reset_index()
                y_col   = "volumen"
                y_label = "Volumen total (kg)"

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily["fecha_dt"], y=daily[y_col],
                mode="lines+markers",
                line=dict(color="#FF3D00", width=3),
                marker=dict(size=8, color="#FF8C00"),
                fill="tozeroy",
                fillcolor="rgba(255,61,0,0.1)",
            ))
            fig.update_layout(
                plot_bgcolor="#1A1A1A", paper_bgcolor="#0D0D0D",
                font=dict(color="#EEEEEE", family="Poppins"),
                xaxis=dict(gridcolor="#2A2A2A", title="Fecha"),
                yaxis=dict(gridcolor="#2A2A2A", title=y_label),
                margin=dict(l=10, r=10, t=20, b=10),
                height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Stats del ejercicio
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Max Peso",  f"{df_ej['peso'].max():.1f} kg")
            c2.metric("Max 1RM",   f"{df_ej['e1rm'].max():.1f} kg")
            c3.metric("Sesiones",  df_ej["fecha"].nunique())
            c4.metric("Vol. Total", f"{df_ej['volumen'].sum():.0f} kg")

            # Volumen semanal
            st.markdown("### 📅 Volumen semanal")
            df_sem = df.copy()
            df_sem["semana"] = pd.to_datetime(df_sem["fecha"]).dt.to_period("W").dt.start_time
            weekly = df_sem.groupby("semana")["volumen"].sum().reset_index()

            fig2 = go.Figure(go.Bar(
                x=weekly["semana"], y=weekly["volumen"],
                marker_color="#FF3D00", opacity=0.85,
            ))
            fig2.update_layout(
                plot_bgcolor="#1A1A1A", paper_bgcolor="#0D0D0D",
                font=dict(color="#EEEEEE", family="Poppins"),
                xaxis=dict(gridcolor="#2A2A2A", title="Semana"),
                yaxis=dict(gridcolor="#2A2A2A", title="Volumen (kg)"),
                margin=dict(l=10, r=10, t=20, b=10),
                height=250,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ══════════════════════════════════════
    #  TAB 3 — RÉCORDS
    # ══════════════════════════════════════
    with tab3:
        df = get_data()
        if df.empty:
            st.info("Sin datos aún. ¡Levanta algo primero!")
        else:
            df = enrich(df)
            st.markdown("### 🏆 Récords Personales (por 1RM estimado)")

            # Filtro por categoría
            todas_cats = ["Todas"] + list(CATEGORIAS.keys()) + ["⚙️ Personalizado"]
            cat_filtro = st.selectbox("Filtrar por categoría", todas_cats, key="rec_cat")

            prs = (df
                   .sort_values("e1rm", ascending=False)
                   .drop_duplicates("ejercicio")
                   .sort_values("e1rm", ascending=False)
                   .reset_index(drop=True))

            if cat_filtro != "Todas":
                if cat_filtro == "⚙️ Personalizado":
                    todos_conocidos = [e for cat in CATEGORIAS.values() for e in cat]
                    prs = prs[~prs["ejercicio"].isin(todos_conocidos)]
                else:
                    prs = prs[prs["ejercicio"].isin(CATEGORIAS[cat_filtro])]

            medals = ["🥇", "🥈", "🥉"]
            for i, (_, pr) in enumerate(prs.iterrows()):
                icono = medals[i] if i < 3 else "🏅"
                st.markdown(
                    f'<div class="pr-card">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<div>'
                    f'  <span style="font-size:1.1rem">{icono} <b>{pr["ejercicio"]}</b></span><br>'
                    f'  <span style="color:#888;font-size:.8rem">📅 {pr["fecha"]}</span>'
                    f'</div>'
                    f'<div style="text-align:right;">'
                    f'  <div style="font-size:1.8rem;font-weight:700;color:#FF3D00">{pr["peso"]} kg</div>'
                    f'  <div style="color:#FF8C00;font-size:.9rem">× {int(pr["reps"])} reps</div>'
                    f'  <div style="color:#888;font-size:.8rem">1RM: {pr["e1rm"]} kg</div>'
                    f'</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    # ══════════════════════════════════════
    #  TAB 4 — HISTORIAL
    # ══════════════════════════════════════
    with tab4:
        df = get_data()
        if df.empty:
            st.info("Sin historial aún.")
        else:
            df = enrich(df)
            st.markdown("### 📋 Historial Completo")

            # Filtros
            c1, c2 = st.columns(2)
            ej_f  = c1.selectbox("Ejercicio", ["Todos"] + sorted(df["ejercicio"].unique()), key="hist_ej")
            fechas_ord = sorted(df["fecha"].unique(), reverse=True)
            fec_f = c2.selectbox("Fecha",    ["Todas"] + [str(f) for f in fechas_ord], key="hist_fec")

            df_f = df.copy()
            if ej_f  != "Todos":
                df_f = df_f[df_f["ejercicio"] == ej_f]
            if fec_f != "Todas":
                df_f = df_f[df_f["fecha"] == datetime.date.fromisoformat(fec_f)]

            df_f = df_f.sort_values(["fecha", "ejercicio", "serie"], ascending=[False, True, True])

            for fecha_dia in df_f["fecha"].unique():
                dia_rows = df_f[df_f["fecha"] == fecha_dia]
                vol_dia  = dia_rows["volumen"].sum()
                with st.expander(
                    f"📅 {fecha_es(fecha_dia)}   —   "
                    f"{dia_rows['ejercicio'].nunique()} ejercicios  |  "
                    f"{len(dia_rows)} series  |  Vol: {vol_dia:.0f} kg"
                ):
                    st.dataframe(
                        dia_rows[["ejercicio", "serie", "peso", "reps", "e1rm", "volumen"]]
                        .rename(columns={
                            "ejercicio": "Ejercicio", "serie":   "Serie",
                            "peso":      "Peso (kg)", "reps":    "Reps",
                            "e1rm":      "1RM est.", "volumen": "Volumen",
                        }),
                        use_container_width=True,
                        hide_index=True,
                    )
                    if st.button(f"🗑️ Borrar sesión del {fecha_dia}", key=f"del_d_{fecha_dia}"):
                        delete_day(fecha_dia)
                        st.rerun()


if __name__ == "__main__":
    main()
