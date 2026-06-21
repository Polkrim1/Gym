import streamlit as st
import pandas as pd
import datetime
import requests
import plotly.graph_objects as go

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
st.set_page_config(page_title="Gym Pro", page_icon="💪", layout="centered")

API_KEY = st.secrets["jsonbin_api_key"]
BIN_ID  = st.secrets["jsonbin_bin_id"]
URL     = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

# ─────────────────────────────────────────
#  CATÁLOGO POR DEFECTO
# ─────────────────────────────────────────
CATEGORIAS_DEFAULT = {
    "🦵 Pierna"  : ["Sentadilla", "Sentadilla Búlgara", "Leg Press", "Extensión de Cuádriceps",
                    "Curl de Femorales", "Hip Thrust", "Peso Muerto Rumano", "Elevación de Gemelos",
                    "Zancadas", "Hack Squat"],
    "💪 Empuje"  : ["Press Banca", "Press Banca Inclinado", "Press Banca Declinado",
                    "Aperturas con Mancuernas", "Press Militar", "Press Arnold",
                    "Elevaciones Laterales", "Elevaciones Frontales",
                    "Fondos en Paralelas", "Extensión de Tríceps", "Press Francés", "Patada de Tríceps"],
    "🏋️ Jalón"  : ["Peso Muerto", "Dominadas", "Jalón al Pecho", "Remo con Barra",
                    "Remo con Mancuerna", "Remo en Polea", "Face Pull", "Pull-over",
                    "Curl de Bíceps", "Curl Martillo", "Curl en Banco Scott", "Encogimientos de Hombros"],
    "🔥 Core"    : ["Plancha", "Crunch", "Russian Twist", "Rueda Abdominal",
                    "Elevación de Piernas", "Dead Bug", "Bird Dog", "Pallof Press"],
    "🏃 Cardio"  : ["Caminata (min)", "Carrera (min)", "Bicicleta (min)",
                    "Elíptica (min)", "Remo (min)", "Saltar la Cuerda (min)", "HIIT (min)"],
}

# ─────────────────────────────────────────
#  FECHA EN ESPAÑOL
# ─────────────────────────────────────────
_DIAS  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
_MESES = ["","enero","febrero","marzo","abril","mayo","junio",
          "julio","agosto","septiembre","octubre","noviembre","diciembre"]

def fecha_es(d):
    return f"{_DIAS[d.weekday()]}, {d.day} de {_MESES[d.month]} {d.year}"

# ─────────────────────────────────────────
#  BASE DE DATOS  (JSONBin)
#
#  Formato en JSONBin:
#    { "records": [...], "cat_custom": {...} }
#
#  Compatible con el formato viejo (lista plana).
# ─────────────────────────────────────────
_EMPTY_DF = pd.DataFrame(columns=["row_id","fecha","ejercicio","peso","reps","serie"])

def load_all():
    """Retorna (df_records, cat_custom). Migra automáticamente del formato viejo."""
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        rec = r.json().get("record", [])

        if isinstance(rec, dict):                     # Formato nuevo
            raw        = rec.get("records", [])
            cat_custom = rec.get("cat_custom", {})
        elif isinstance(rec, list):                   # Formato viejo
            raw        = rec
            cat_custom = {}
        else:
            return _EMPTY_DF.copy(), {}

        if not raw:
            return _EMPTY_DF.copy(), cat_custom

        df = pd.DataFrame(raw)
        df["fecha"]  = pd.to_datetime(df["fecha"]).dt.date
        df["peso"]   = pd.to_numeric(df["peso"],  errors="coerce").fillna(0)
        df["reps"]   = pd.to_numeric(df["reps"],  errors="coerce").fillna(0).astype(int)
        if "serie"   not in df.columns: df["serie"]  = 1
        if "row_id"  not in df.columns: df["row_id"] = range(len(df))
        df["row_id"] = df["row_id"].astype(int)
        return df, cat_custom

    except Exception:
        return _EMPTY_DF.copy(), {}


def save_all(df: pd.DataFrame, cat_custom: dict):
    rec = df.copy()
    rec["fecha"] = rec["fecha"].astype(str)
    requests.put(URL, json={"records": rec.to_dict(orient="records"),
                             "cat_custom": cat_custom},
                 headers=HEADERS, timeout=10)


def get_all_cats(cat_custom: dict) -> dict:
    """
    Fusiona el catálogo por defecto con las personalizaciones del usuario.
    cat_custom guarda la lista COMPLETA de una categoría cuando ha sido modificada.
    Las categorías con lista vacía se omiten (fueron eliminadas).
    """
    result = {}
    for cat, default_ejs in CATEGORIAS_DEFAULT.items():
        ejs = cat_custom.get(cat, default_ejs)
        if ejs:
            result[cat] = ejs
    for cat, ejs in cat_custom.items():
        if cat not in result and ejs:
            result[cat] = ejs
    return result


# ─────────────────────────────────────────
#  CÁLCULOS
# ─────────────────────────────────────────
def e1rm(peso, reps):
    """Fórmula de Epley."""
    return round(peso * (1 + reps / 30), 1) if reps > 1 else float(peso)

def enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["e1rm"]    = df.apply(lambda r: e1rm(r["peso"], r["reps"]), axis=1)
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
        background-color: #0D0D0D; color: #EEEEEE;
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

      /* Serie row */
      .serie-row {
        background: #1E1E1E; border-radius: 10px; padding: 10px 14px;
        margin-bottom: 6px; border-left: 3px solid #FF3D00;
        display: flex; justify-content: space-between; align-items: center;
      }

      /* Exercise chips */
      .ej-chip {
        display: inline-block; background: #1E1E1E; border: 1px solid #2A2A2A;
        border-radius: 20px; padding: 4px 12px; margin: 3px;
        font-size: 0.82rem; color: #CCC;
      }
      .ej-chip-custom {
        display: inline-block; background: #1E1E1E; border: 1px solid #FF3D00;
        border-radius: 20px; padding: 4px 12px; margin: 3px;
        font-size: 0.82rem; color: #FF8C00;
      }

      /* Title */
      h1 {
        font-size: 2rem; font-weight: 700;
        background: linear-gradient(135deg,#FF3D00,#FF8C00);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0;
      }
      [data-testid="stMetricValue"] { font-size: 1.4rem !important; color: #FF3D00; }
      .stButton > button {
        background: #FF3D00; color: #fff; border: none;
        border-radius: 10px; font-weight: 600; transition: background .2s;
      }
      .stButton > button:hover { background: #FF6130; }
      [data-testid="stExpander"] { border: 1px solid #2A2A2A; border-radius: 12px; }
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

    # Carga única de datos por render
    df_all, cat_custom = load_all()
    cats = get_all_cats(cat_custom)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Registro", "📊 Progreso", "🏆 Récords", "📋 Historial", "⚙️ Ejercicios"
    ])

    # ══════════════════════════════════════
    #  TAB 1 — REGISTRO
    # ══════════════════════════════════════
    with tab1:
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

        with st.expander("➕ Agregar Serie", expanded=True):
            cat_list = list(cats.keys())
            cat      = st.selectbox("Categoría", cat_list, key="cat_sel")
            ejercicio = st.selectbox("Ejercicio", cats[cat], key="ej_sel")

            col_p, col_r = st.columns(2)
            peso = col_p.number_input("Peso (kg)", min_value=0.0, step=2.5, value=60.0)
            reps = col_r.number_input("Reps", min_value=1, max_value=200, step=1, value=10)

            m1, m2 = st.columns(2)
            m1.metric("1RM estimado", f"{e1rm(peso, reps)} kg")
            m2.metric("Volumen",      f"{peso * reps:.0f} kg")

            if st.button("💾 Guardar Serie", use_container_width=True):
                df_r, cc = load_all()
                mask      = (df_r["fecha"] == st.session_state.fecha_sel) & (df_r["ejercicio"] == ejercicio)
                serie_num = int(df_r[mask]["serie"].max() + 1) if mask.any() else 1
                next_id   = int(df_r["row_id"].max() + 1) if not df_r.empty else 0
                nueva_f   = pd.DataFrame({"row_id": [next_id],
                                          "fecha":     [st.session_state.fecha_sel],
                                          "ejercicio": [ejercicio],
                                          "peso":      [peso],
                                          "reps":      [reps],
                                          "serie":     [serie_num]})
                save_all(pd.concat([df_r, nueva_f], ignore_index=True), cc)
                st.success("¡Serie guardada! 🔥")
                st.rerun()

        # Registro del día
        if not df_all.empty:
            dia = enrich(df_all[df_all["fecha"] == st.session_state.fecha_sel].copy())
            if not dia.empty:
                s1, s2, s3 = st.columns(3)
                s1.metric("Series",        len(dia))
                s2.metric("Ejercicios",    dia["ejercicio"].nunique())
                s3.metric("Volumen Total", f"{dia['volumen'].sum():.0f} kg")

                st.markdown("### Series del día")
                for ej in dia["ejercicio"].unique():
                    ej_d = dia[dia["ejercicio"] == ej]
                    st.markdown(f"**{ej}** — Volumen: {ej_d['volumen'].sum():.0f} kg")
                    for _, row in ej_d.iterrows():
                        cA, cB = st.columns([7, 1])
                        cA.markdown(
                            f'<div class="serie-row">'
                            f'<span>Serie {int(row["serie"])} &nbsp;'
                            f'<b>{row["peso"]} kg × {int(row["reps"])} reps</b></span>'
                            f'<span style="color:#888;font-size:.8rem">1RM: {row["e1rm"]} kg</span>'
                            f'</div>', unsafe_allow_html=True)
                        if cB.button("🗑️", key=f"del_{row['row_id']}"):
                            df_r, cc = load_all()
                            save_all(df_r[df_r["row_id"] != int(row["row_id"])], cc)
                            st.rerun()

                st.markdown("---")
                if st.button("🗑️ Borrar todo el día", use_container_width=True):
                    df_r, cc = load_all()
                    save_all(df_r[df_r["fecha"] != st.session_state.fecha_sel], cc)
                    st.rerun()
            else:
                st.info("💤 Sin registros para este día. ¡A entrenar!")
        else:
            st.info("💤 No hay datos aún. ¡Empieza tu primer entrenamiento!")

    # ══════════════════════════════════════
    #  TAB 2 — PROGRESO
    # ══════════════════════════════════════
    with tab2:
        if df_all.empty:
            st.info("Sin datos suficientes para mostrar progreso.")
        else:
            df_e = enrich(df_all)
            st.markdown("### 📊 Progreso por ejercicio")

            ej_sel  = st.selectbox("Ejercicio", sorted(df_e["ejercicio"].unique()), key="prog_ej")
            metrica = st.radio("Métrica", ["Peso máximo", "1RM estimado", "Volumen total"], horizontal=True)

            df_ej = df_e[df_e["ejercicio"] == ej_sel].copy()
            df_ej["fecha_dt"] = pd.to_datetime(df_ej["fecha"])

            if metrica == "Peso máximo":
                daily = df_ej.groupby("fecha_dt")["peso"].max().reset_index()
                y_col, y_label = "peso", "Peso (kg)"
            elif metrica == "1RM estimado":
                daily = df_ej.groupby("fecha_dt")["e1rm"].max().reset_index()
                y_col, y_label = "e1rm", "1RM estimado (kg)"
            else:
                daily = df_ej.groupby("fecha_dt")["volumen"].sum().reset_index()
                y_col, y_label = "volumen", "Volumen total (kg)"

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=daily["fecha_dt"], y=daily[y_col],
                mode="lines+markers",
                line=dict(color="#FF3D00", width=3),
                marker=dict(size=8, color="#FF8C00"),
                fill="tozeroy", fillcolor="rgba(255,61,0,0.1)",
            ))
            fig.update_layout(
                plot_bgcolor="#1A1A1A", paper_bgcolor="#0D0D0D",
                font=dict(color="#EEEEEE", family="Poppins"),
                xaxis=dict(gridcolor="#2A2A2A", title="Fecha"),
                yaxis=dict(gridcolor="#2A2A2A", title=y_label),
                margin=dict(l=10, r=10, t=20, b=10), height=300,
            )
            st.plotly_chart(fig, use_container_width=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Max Peso",   f"{df_ej['peso'].max():.1f} kg")
            c2.metric("Max 1RM",    f"{df_ej['e1rm'].max():.1f} kg")
            c3.metric("Sesiones",   df_ej["fecha"].nunique())
            c4.metric("Vol. Total", f"{df_ej['volumen'].sum():.0f} kg")

            st.markdown("### 📅 Volumen semanal (todos los ejercicios)")
            df_sem            = df_e.copy()
            df_sem["semana"]  = pd.to_datetime(df_sem["fecha"]).dt.to_period("W").dt.start_time
            weekly            = df_sem.groupby("semana")["volumen"].sum().reset_index()
            fig2 = go.Figure(go.Bar(x=weekly["semana"], y=weekly["volumen"],
                                    marker_color="#FF3D00", opacity=0.85))
            fig2.update_layout(
                plot_bgcolor="#1A1A1A", paper_bgcolor="#0D0D0D",
                font=dict(color="#EEEEEE", family="Poppins"),
                xaxis=dict(gridcolor="#2A2A2A", title="Semana"),
                yaxis=dict(gridcolor="#2A2A2A", title="Volumen (kg)"),
                margin=dict(l=10, r=10, t=20, b=10), height=250,
            )
            st.plotly_chart(fig2, use_container_width=True)

    # ══════════════════════════════════════
    #  TAB 3 — RÉCORDS
    # ══════════════════════════════════════
    with tab3:
        if df_all.empty:
            st.info("Sin datos aún. ¡Levanta algo primero!")
        else:
            df_e = enrich(df_all)
            st.markdown("### 🏆 Récords Personales (por 1RM estimado)")

            cat_filtro = st.selectbox("Filtrar por categoría",
                                       ["Todas"] + list(cats.keys()), key="rec_cat")

            prs = (df_e
                   .sort_values("e1rm", ascending=False)
                   .drop_duplicates("ejercicio")
                   .sort_values("e1rm", ascending=False)
                   .reset_index(drop=True))

            if cat_filtro != "Todas":
                prs = prs[prs["ejercicio"].isin(cats.get(cat_filtro, []))]

            medals = ["🥇", "🥈", "🥉"]
            for i, (_, pr) in enumerate(prs.iterrows()):
                icono = medals[i] if i < 3 else "🏅"
                st.markdown(
                    f'<div class="pr-card">'
                    f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                    f'<div><span style="font-size:1.1rem">{icono} <b>{pr["ejercicio"]}</b></span><br>'
                    f'<span style="color:#888;font-size:.8rem">📅 {pr["fecha"]}</span></div>'
                    f'<div style="text-align:right;">'
                    f'<div style="font-size:1.8rem;font-weight:700;color:#FF3D00">{pr["peso"]} kg</div>'
                    f'<div style="color:#FF8C00;font-size:.9rem">× {int(pr["reps"])} reps</div>'
                    f'<div style="color:#888;font-size:.8rem">1RM: {pr["e1rm"]} kg</div>'
                    f'</div></div></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════
    #  TAB 4 — HISTORIAL
    # ══════════════════════════════════════
    with tab4:
        if df_all.empty:
            st.info("Sin historial aún.")
        else:
            df_e = enrich(df_all)
            st.markdown("### 📋 Historial Completo")

            c1, c2 = st.columns(2)
            ej_f  = c1.selectbox("Ejercicio", ["Todos"] + sorted(df_e["ejercicio"].unique()), key="hist_ej")
            fec_f = c2.selectbox("Fecha",
                                  ["Todas"] + [str(f) for f in sorted(df_e["fecha"].unique(), reverse=True)],
                                  key="hist_fec")

            df_f = df_e.copy()
            if ej_f  != "Todos": df_f = df_f[df_f["ejercicio"] == ej_f]
            if fec_f != "Todas": df_f = df_f[df_f["fecha"] == datetime.date.fromisoformat(fec_f)]
            df_f = df_f.sort_values(["fecha","ejercicio","serie"], ascending=[False,True,True])

            for fecha_dia in df_f["fecha"].unique():
                rows = df_f[df_f["fecha"] == fecha_dia]
                with st.expander(
                    f"📅 {fecha_es(fecha_dia)}  —  "
                    f"{rows['ejercicio'].nunique()} ejercicios  |  "
                    f"{len(rows)} series  |  Vol: {rows['volumen'].sum():.0f} kg"
                ):
                    st.dataframe(
                        rows[["ejercicio","serie","peso","reps","e1rm","volumen"]]
                        .rename(columns={"ejercicio":"Ejercicio","serie":"Serie",
                                         "peso":"Peso (kg)","reps":"Reps",
                                         "e1rm":"1RM est.","volumen":"Volumen"}),
                        use_container_width=True, hide_index=True)
                    if st.button(f"🗑️ Borrar sesión del {fecha_dia}", key=f"del_d_{fecha_dia}"):
                        df_r, cc = load_all()
                        save_all(df_r[df_r["fecha"] != fecha_dia], cc)
                        st.rerun()

    # ══════════════════════════════════════
    #  TAB 5 — GESTIÓN DE EJERCICIOS
    # ══════════════════════════════════════
    with tab5:
        st.markdown("### ⚙️ Gestión de Ejercicios")

        # Qué ejercicios son "por defecto" vs "custom"
        ejs_default = {e for cat in CATEGORIAS_DEFAULT.values() for e in cat}

        # ── Agregar ejercicio ──────────────────
        with st.expander("➕ Agregar Ejercicio", expanded=True):
            modo = st.radio("¿Dónde agregar?",
                            ["A categoría existente", "Crear nueva categoría"],
                            horizontal=True, key="modo_add")

            if modo == "A categoría existente":
                cat_add  = st.selectbox("Categoría", list(cats.keys()), key="cat_add")
                nuevo_ej = st.text_input("Nombre del ejercicio", key="nuevo_ej",
                                          placeholder="ej. Sentadilla Sumo...")

                if st.button("➕ Agregar ejercicio", use_container_width=True, key="btn_add_ej"):
                    nuevo_ej = nuevo_ej.strip()
                    if not nuevo_ej:
                        st.error("Escribe el nombre del ejercicio.")
                    elif nuevo_ej in cats.get(cat_add, []):
                        st.warning("Ese ejercicio ya existe en esta categoría.")
                    else:
                        df_r, cc = load_all()
                        cc[cat_add] = list(cats.get(cat_add, [])) + [nuevo_ej]
                        save_all(df_r, cc)
                        st.success(f"✅ '{nuevo_ej}' agregado a {cat_add}")
                        st.rerun()

            else:  # Nueva categoría
                nueva_cat = st.text_input("Nombre de la nueva categoría", key="nueva_cat",
                                           placeholder="ej. 🧘 Movilidad")
                primer_ej = st.text_input("Primer ejercicio", key="primer_ej",
                                           placeholder="ej. Estiramiento de cadera")

                if st.button("🆕 Crear categoría", use_container_width=True, key="btn_add_cat"):
                    nueva_cat = nueva_cat.strip()
                    primer_ej = primer_ej.strip()
                    if not nueva_cat or not primer_ej:
                        st.error("Escribe el nombre de la categoría y al menos un ejercicio.")
                    elif nueva_cat in cats:
                        st.warning("Esa categoría ya existe.")
                    else:
                        df_r, cc = load_all()
                        cc[nueva_cat] = [primer_ej]
                        save_all(df_r, cc)
                        st.success(f"✅ Categoría '{nueva_cat}' creada con '{primer_ej}'.")
                        st.rerun()

        # ── Eliminar ejercicio ─────────────────
        with st.expander("🗑️ Eliminar Ejercicio"):
            if not cats:
                st.info("No hay ejercicios que eliminar.")
            else:
                cat_del = st.selectbox("Categoría", list(cats.keys()), key="cat_del")
                ej_del  = st.selectbox("Ejercicio", cats.get(cat_del, []), key="ej_del")

                n_regs = 0 if df_all.empty else len(df_all[df_all["ejercicio"] == ej_del])
                if n_regs > 0:
                    st.warning(f"⚠️ Este ejercicio tiene **{n_regs} registros** en tu historial. "
                               "Se quitará del catálogo, pero tu historial se conserva.")

                if st.button("🗑️ Eliminar del catálogo", use_container_width=True, key="btn_del_ej"):
                    df_r, cc = load_all()
                    lista_nueva = [e for e in cats.get(cat_del, []) if e != ej_del]
                    # Guardar lista nueva (vacía = categoría oculta)
                    cc[cat_del] = lista_nueva
                    save_all(df_r, cc)
                    st.success(f"✅ '{ej_del}' eliminado.")
                    if not lista_nueva:
                        st.info(f"La categoría '{cat_del}' quedó vacía y se ocultó del menú.")
                    st.rerun()

        # ── Eliminar categoría completa ────────
        with st.expander("🗂️ Eliminar Categoría Completa"):
            if not cats:
                st.info("No hay categorías que eliminar.")
            else:
                cat_del_all = st.selectbox("Categoría a eliminar", list(cats.keys()), key="cat_del_all")
                n_ejs_cat   = len(cats.get(cat_del_all, []))
                n_regs_cat  = 0 if df_all.empty else len(
                    df_all[df_all["ejercicio"].isin(cats.get(cat_del_all, []))])

                st.markdown(f"Contiene **{n_ejs_cat} ejercicios**.")
                if n_regs_cat > 0:
                    st.warning(f"⚠️ Hay **{n_regs_cat} registros** de esta categoría en tu historial. "
                               "Se oculta del catálogo, el historial no se toca.")

                if st.button("🗑️ Eliminar categoría", use_container_width=True, key="btn_del_cat"):
                    df_r, cc = load_all()
                    cc[cat_del_all] = []          # Lista vacía = oculta
                    save_all(df_r, cc)
                    st.success(f"✅ Categoría '{cat_del_all}' eliminada.")
                    st.rerun()

        # ── Restaurar defaults ─────────────────
        with st.expander("♻️ Restaurar Catálogo por Defecto"):
            st.markdown("Vuelve al catálogo original. **Tus registros de entrenamiento NO se borran.**")
            if st.button("♻️ Restaurar todo", use_container_width=True, key="btn_reset"):
                df_r, _ = load_all()
                save_all(df_r, {})          # cat_custom vacío = todo default
                st.success("✅ Catálogo restaurado.")
                st.rerun()

        # ── Catálogo actual ────────────────────
        st.markdown("---")
        st.markdown("### 📋 Catálogo Actual")

        for cat_name, ejs in cats.items():
            if not ejs:
                continue
            st.markdown(f"**{cat_name}** — {len(ejs)} ejercicios")
            chips = ""
            for e in ejs:
                cls   = "ej-chip" if e in ejs_default else "ej-chip-custom"
                chips += f'<span class="{cls}">{e}</span>'
            st.markdown(f'<div style="margin-bottom:14px">{chips}</div>', unsafe_allow_html=True)

        st.markdown("<p style='color:#555;font-size:.8rem'>"
                    "🟠 naranja = ejercicio personalizado &nbsp;|&nbsp; ⬜ gris = ejercicio por defecto"
                    "</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
