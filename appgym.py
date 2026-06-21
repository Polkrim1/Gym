import streamlit as st
import requests
import json
import pandas as pd
import datetime
import calendar
import plotly.express as px

# ==========================================
# CONFIGURACIÓN DE PÁGINA (Mobile First)
# ==========================================
st.set_page_config(
    page_title="Gym Tracker Premium",
    page_icon="💪",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================
# INYECCIÓN DE CSS (Dark Mode, UI Premium & Mobile First)
# ==========================================
def inject_css():
    st.markdown("""
    <style>
        /* Fondo principal y tipografía */
        .stApp {
            background-color: #0d1117;
            color: #c9d1d9;
        }
        
        /* Ocultar elementos de UI de Streamlit para efecto PWA */
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Optimización de los botones del Calendario */
        div.stButton > button {
            padding: 0px !important;
            height: 40px !important;
            font-size: 0.85rem !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border-radius: 6px !important;
        }

        /* Botón de día normal (Descanso) */
        div.stButton > button[kind="secondary"] {
            background-color: #161b22;
            color: #c9d1d9;
            border: 1px solid #30363d;
        }

        /* Botón de día Entrenado (Verde Neón Premium) */
        div.stButton > button[kind="primary"] {
            background-color: #39FF14 !important;
            color: #000000 !important;
            border: none !important;
            box-shadow: 0 0 10px rgba(57,255,20,0.4);
        }

        /* Tarjetas de Récords (PRs) Premium */
        .pr-card {
            background-color: #161b22;
            border-left: 5px solid #39FF14;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }
        .pr-title {
            color: #8A2BE2;
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 5px;
            text-transform: uppercase;
        }
        .pr-weight {
            color: #39FF14;
            font-size: 2.2rem;
            font-weight: 900;
        }
        .pr-reps {
            color: #8b949e;
            font-size: 0.9rem;
        }

        /* ===================================================
           MODO PWA MÓVIL: Evitar el scroll vertical de columnas
           =================================================== */
        @media (max-width: 640px) {
            /* Forzar a todos los contenedores de columnas a mantenerse en fila */
            [data-testid="stHorizontalBlock"] {
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                gap: 0.1rem !important; /* Juntar los botones para aprovechar espacio */
            }
            
            /* Quitar el ancho mínimo para que las 7 columnas quepan en pantalla */
            [data-testid="column"] {
                min-width: 0 !important;
                padding: 0 1px !important; 
            }

            /* Hacer el texto del botón del día ligeramente más pequeño para evitar cortes */
            div.stButton > button {
                font-size: 0.75rem !important;
                height: 35px !important; 
            }
        }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# LÓGICA DE BASE DE DATOS (JSONBin.io)
# ==========================================
DEFAULT_DATA = {
    "ejercicios": [],
    "historial_marcas": [],
    "asistencia": []
}

def get_headers():
    try:
        return {
            "Content-Type": "application/json",
            "X-Master-Key": st.secrets["jsonbin_api_key"]
        }
    except KeyError:
        return None

def get_bin_url():
    try:
        return f"https://api.jsonbin.io/v3/b/{st.secrets['jsonbin_bin_id']}"
    except KeyError:
        return None

def load_data():
    headers = get_headers()
    url = get_bin_url()
    
    if not headers or not url:
        return DEFAULT_DATA

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('record', DEFAULT_DATA)
        else:
            return DEFAULT_DATA
    except Exception:
        return DEFAULT_DATA

def save_data(data):
    st.session_state.data = data
    headers = get_headers()
    url = get_bin_url()
    if headers and url:
        try:
            requests.put(url, json=data, headers=headers)
        except Exception:
            pass

# ==========================================
# INICIALIZACIÓN DE ESTADOS
# ==========================================
if 'data' not in st.session_state:
    st.session_state.data = load_data()

if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

# NUEVO: Estado para controlar el mes que se está visualizando
if 'view_date' not in st.session_state:
    st.session_state.view_date = datetime.date.today().replace(day=1)
# ==========================================
# COMPONENTE: CALENDARIO INTERACTIVO
# ==========================================
def render_interactive_calendar(data):
    meses_espanol = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    view_date = st.session_state.view_date
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(view_date.year, view_date.month)
    
    st.markdown("### 📅 Asistencia")
    
# --- Controles de Navegación de Meses ---
    # Dividimos en 4 columnas: Izq, Centro (Mes/Año), Der, Reset
    col_prev, col_mes, col_next, col_reset = st.columns([1, 3, 1, 1])
    
    with col_prev:
        if st.button("⬅️", use_container_width=True):
            first_day = view_date.replace(day=1)
            prev_month = first_day - datetime.timedelta(days=1)
            st.session_state.view_date = prev_month.replace(day=1)
            st.rerun()
            
    with col_mes:
        mes_actual = meses_espanol[view_date.month - 1]
        st.markdown(f"<div style='text-align:center; font-size:1rem; font-weight:bold; color:#8A2BE2; padding-top:10px;'>{mes_actual[:3].upper()} {str(view_date.year)[-2:]}</div>", unsafe_allow_html=True)
        
    with col_next:
        if st.button("➡️", use_container_width=True):
            days_in_month = calendar.monthrange(view_date.year, view_date.month)[1]
            last_day = view_date.replace(day=days_in_month)
            next_month = last_day + datetime.timedelta(days=1)
            st.session_state.view_date = next_month.replace(day=1)
            st.rerun()

    with col_reset:
        if st.button("🏠", help="Volver a hoy", use_container_width=True):
            st.session_state.view_date = datetime.date.today().replace(day=1)
            st.session_state.selected_date = datetime.date.today()
            st.rerun()
            
    st.write("") # Espaciador ligero
    
    # --- Cabecera fija de días de la semana ---
    cols_h = st.columns(7, gap="small")
    days_names = ["L", "M", "X", "J", "V", "S", "D"]
    for i, name in enumerate(days_names):
        cols_h[i].markdown(f"<div style='text-align:center; font-size:0.75rem; color:#8b949e; font-weight:bold; margin-bottom:5px;'>{name}</div>", unsafe_allow_html=True)
    
    # --- Renderizado de la cuadrícula interactiva ---
    for week in month_days:
        cols = st.columns(7, gap="small")
        for i, day in enumerate(week):
            if day.month != view_date.month:
                cols[i].write("")  # Espacio vacío para días fuera del mes en vista
                continue
            
            day_str = day.strftime("%Y-%m-%d")
            is_trained = day_str in data.get("asistencia", [])
            is_selected = (st.session_state.selected_date == day)
            
            btn_type = "primary" if is_trained else "secondary"
            label = f"📍 {day.day}" if is_selected else f"{day.day}"
            
            # Key único para evitar conflictos entre meses
            if cols[i].button(label, key=f"cal_{view_date.year}_{view_date.month}_{day.day}", type=btn_type, use_container_width=True):
                st.session_state.selected_date = day
                st.rerun()

# ==========================================
# ESTRUCTURA PRINCIPAL DE LA APP
# ==========================================
def main():
    inject_css()
    
    st.markdown("<h1 style='text-align: center; color: #39FF14; font-size: 2rem; margin-bottom:0;'>GYM TRACKER</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 Diario", "🏆 PRs", "📈 Progreso", "⚙️ Ajustes"])
    
    data = st.session_state.data
    hoy_str = datetime.date.today().strftime("%Y-%m-%d")

    # ------------------------------------------
    # TAB 1: CALENDARIO INTERACTIVO & DETALLES
    # ------------------------------------------
    with tab1:
        # 1. Renderizar la cuadrícula interactiva
        render_interactive_calendar(data)
        
        # 2. Panel Dinámico del Día Seleccionado
        sel_date = st.session_state.selected_date
        sel_date_str = sel_date.strftime("%Y-%m-%d")
        is_trained_sel = sel_date_str in data.get("asistencia", [])
        
        st.divider()
        st.markdown(f"#### Detalle del día: `{sel_date.strftime('%d / %m / %Y')}`")
        
        # Tarjeta informativa del estado del día
        status_color = "#39FF14" if is_trained_sel else "#8b949e"
        status_text = "🟢 ENTRENADO" if is_trained_sel else "⚪ CONTROL DE DESCANSO"
        
        st.markdown(f"""
        <div style='background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 15px;'>
            <div style='font-size: 0.8rem; color: #8b949e; text-transform: uppercase; font-weight: bold;'>Registro de Asistencia</div>
            <div style='font-size: 1.3rem; font-weight: 900; color: {status_color}; margin-top: 5px;'>{status_text}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Controles para añadir o quitar asistencia del día seleccionado
        col_btn1, col_btn2 = st.columns(2)
        if not is_trained_sel:
            if col_btn1.button("✅ Marcar Asistencia", use_container_width=True, type="primary"):
                data.setdefault("asistencia", []).append(sel_date_str)
                save_data(data)
                st.rerun()
        else:
            if col_btn2.button("❌ Quitar Asistencia", use_container_width=True):
                data["asistencia"].remove(sel_date_str)
                save_data(data)
                st.rerun()
                
        # Mostrar las marcas/series ejecutadas específicamente ese día
        marcas_dia = [m for m in data.get("historial_marcas", []) if m["fecha"] == sel_date_str]
        if marcas_dia:
            st.markdown("<p style='color:#39FF14; font-weight:bold; margin-top:15px; margin-bottom:5px;'>💪 Series completadas:</p>", unsafe_allow_html=True)
            for m in marcas_dia:
                st.markdown(f"• **{m['ejercicio']}**: {m['peso']} kg x {m['reps']} reps")
        else:
            st.markdown("<p style='color:#8b949e; font-style:italic; margin-top:15px;'>No hay series registradas en esta fecha.</p>", unsafe_allow_html=True)

        # 3. Formulario para registrar nuevas series (Se guardan en el día seleccionado)
        st.divider()
        st.markdown(f"### Registrar Serie para el {sel_date.strftime('%d/%m')}")
        ejercicios_list = [e["nombre"] for e in data.get("ejercicios", [])]
        
        if not ejercicios_list:
            st.info("Ve a Ajustes para agregar tus primeros ejercicios.")
        else:
            with st.form("registro_serie", clear_on_submit=True):
                ejercicio_sel = st.selectbox("Ejercicio", ejercicios_list)
                col1, col2 = st.columns(2)
                peso_val = col1.number_input("Peso (kg)", min_value=0.0, step=1.0)
                reps_val = col2.number_input("Repeticiones Max", min_value=1, step=1)
                
                if st.form_submit_button("Guardar Marca en Historial", use_container_width=True):
                    nuevo_registro = {
                        "id": str(datetime.datetime.now().timestamp()),
                        "ejercicio": ejercicio_sel,
                        "fecha": sel_date_str,
                        "peso": peso_val,
                        "reps": reps_val
                    }
                    data.setdefault("historial_marcas", []).append(nuevo_registro)
                    save_data(data)
                    st.success(f"Guardado en {sel_date_str}!")
                    st.rerun()

    # ------------------------------------------
    # TAB 2: RÉCORDS PERSONALES (PRs)
    # ------------------------------------------
    with tab2:
        st.markdown("### Récords Históricos")
        historial = data.get("historial_marcas", [])
        
        if not historial:
            st.info("Aún no hay marcas registradas.")
        else:
            df = pd.DataFrame(historial)
            max_prs = df.loc[df.groupby('ejercicio')['peso'].idxmax()]
            
            for _, row in max_prs.iterrows():
                card_html = f"""
                <div class="pr-card">
                    <div class="pr-title">{row['ejercicio']}</div>
                    <div class="pr-weight">{row['peso']} <span style="font-size:1rem; color:#8b949e;">kg</span></div>
                    <div class="pr-reps">Récord logrado con {row['reps']} RM el {row['fecha']}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

    # ------------------------------------------
    # TAB 3: GRÁFICAS DE PROGRESO
    # ------------------------------------------
    with tab3:
        st.markdown("### Evolución de Marcas")
        ejercicios_registrados = list(set([r["ejercicio"] for r in data.get("historial_marcas", [])]))
        
        if not ejercicios_registrados:
            st.info("Registra marcas para ver tus gráficas de progreso.")
        else:
            grafica_ej = st.selectbox("Selecciona un ejercicio", ejercicios_registrados)
            
            df_hist = pd.DataFrame(data["historial_marcas"])
            df_filtrado = df_hist[df_hist["ejercicio"] == grafica_ej].sort_values("fecha")
            
            if not df_filtrado.empty:
                fig = px.line(
                    df_filtrado, 
                    x="fecha", 
                    y="peso", 
                    markers=True,
                    hover_data=["reps"],
                    color_discrete_sequence=["#39FF14"]
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#c9d1d9",
                    xaxis_title="Fecha",
                    yaxis_title="Peso (kg)",
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                fig.update_xaxes(showgrid=False)
                fig.update_yaxes(gridcolor="#30363d")
                
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ------------------------------------------
    # TAB 4: AJUSTES & ROBUSTEZ
    # ------------------------------------------
    with tab4:
        st.markdown("### Gestión de Datos")
        
        with st.expander("➕ Añadir Nuevo Ejercicio"):
            with st.form("nuevo_ejercicio"):
                nom_ej = st.text_input("Nombre del Ejercicio")
                grp_ej = st.selectbox("Grupo Muscular", ["Pecho", "Espalda", "Pierna", "Hombro", "Brazos", "Core", "Otro"])
                if st.form_submit_button("Guardar Ejercicio"):
                    if nom_ej:
                        data.setdefault("ejercicios", []).append({"nombre": nom_ej, "grupo": grp_ej})
                        save_data(data)
                        st.success("Ejercicio añadido.")
                        st.rerun()
        
        with st.expander("🗑️ Eliminar Ejercicio"):
            if data.get("ejercicios"):
                ej_a_borrar = st.selectbox("Selecciona ejercicio a borrar", [e["nombre"] for e in data["ejercicios"]])
                if st.button("Eliminar Ejercicio Seleccionado"):
                    data["ejercicios"] = [e for e in data["ejercicios"] if e["nombre"] != ej_a_borrar]
                    save_data(data)
                    st.success("Ejercicio eliminado.")
                    st.rerun()
            else:
                st.write("No hay ejercicios para borrar.")
                
        with st.expander("⚠️ Borrar Registro Histórico"):
            if data.get("historial_marcas"):
                opciones_borrar = {f"{r['fecha']} - {r['ejercicio']} ({r['peso']}kg)": r['id'] for r in data["historial_marcas"]}
                reg_a_borrar = st.selectbox("Selecciona registro erróneo", list(opciones_borrar.keys()))
                
                if st.button("Eliminar Registro"):
                    id_borrar = opciones_borrar[reg_a_borrar]
                    data["historial_marcas"] = [r for r in data["historial_marcas"] if r["id"] != id_borrar]
                    save_data(data)
                    st.success("Registro eliminado exitosamente.")
                    st.rerun()
            else:
                st.write("No hay registros en el historial.")

if __name__ == "__main__":
    main()