import streamlit as st
import pandas as pd
import datetime
import requests
import json

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gym Pro", page_icon="💪", layout="centered")

# --- CONEXIÓN CON JSONBIN ---
API_KEY = st.secrets["jsonbin_api_key"]
BIN_ID = st.secrets["jsonbin_bin_id"]
URL = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {"X-Master-Key": API_KEY, "Content-Type": "application/json"}

def get_data():
    try:
        response = requests.get(URL, headers=HEADERS)
        data = response.json()
        if 'record' in data:
            return pd.DataFrame(data['record'])
    except:
        pass
    return pd.DataFrame(columns=['fecha', 'ejercicio', 'peso', 'reps'])

def save_data(df):
    requests.put(URL, json=df.to_dict(orient='records'), headers=HEADERS)

def add_serie(fecha, ejercicio, peso, reps):
    df = get_data()
    nueva_fila = pd.DataFrame({'fecha': [fecha], 'ejercicio': [ejercicio], 'peso': [peso], 'reps': [reps]})
    df = pd.concat([df, nueva_fila], ignore_index=True)
    save_data(df)

def delete_day(fecha):
    df = get_data()
    df['fecha'] = pd.to_datetime(df['fecha']).dt.date
    df_nuevo = df[df['fecha'] != fecha]
    save_data(df_nuevo)

# --- DISEÑO CSS ---
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        html, body, [data-testid="stAppViewContainer"] { font-family: 'Poppins', sans-serif !important; background-color: #111111; color: #EEEEEE; }
        header, [data-testid="stToolbar"], footer { visibility: hidden; display: none !important; }
        .pr-card { background-color: #1A1A1A; border-radius: 15px; padding: 15px; margin-bottom: 10px; border: 1px solid #333333; }
        
        @media (max-width: 640px) {
            [data-testid="stHorizontalBlock"] { flex-direction: column !important; gap: 5px !important; }
            [data-testid="column"] { width: 100% !important; }
        }
    </style>
    """, unsafe_allow_html=True)

# --- APP PRINCIPAL ---
def main():
    inject_css()
    st.title("🔥 GYM PRO")
    
    if 'fecha_form' not in st.session_state:
        st.session_state.fecha_form = datetime.date.today()

    tab1, tab2 = st.tabs(["📝 REGISTRO", "🏆 RÉCORDS"])
    
    with tab1:
        st.subheader("Selecciona fecha")
        c1, c2, c3 = st.columns(3)
        if c1.button("Hoy", use_container_width=True): st.session_state.fecha_form = datetime.date.today()
        if c2.button("Ayer", use_container_width=True): st.session_state.fecha_form = datetime.date.today() - datetime.timedelta(days=1)
        st.session_state.fecha_form = c3.date_input("Otra", value=st.session_state.fecha_form, label_visibility="collapsed")
        
        with st.expander("➕ Añadir Ejercicio", expanded=True):
            ej = st.selectbox("Ejercicio", ["Sentadilla", "Press Banca", "Peso Muerto", "Press Militar"])
            p = st.number_input("Peso (kg)", min_value=0.0, step=2.5)
            r = st.number_input("Reps", min_value=1, step=1)
            if st.button("Guardar Serie", use_container_width=True):
                add_serie(st.session_state.fecha_form, ej, p, r)
                st.rerun()

        st.markdown(f"---")
        df = get_data()
        if not df.empty:
            df['fecha'] = pd.to_datetime(df['fecha']).dt.date
            dia = df[df['fecha'] == st.session_state.fecha_form]
            if not dia.empty:
                st.dataframe(dia[['ejercicio', 'peso', 'reps']], use_container_width=True, hide_index=True)
                if st.button("🗑️ Borrar día"):
                    delete_day(st.session_state.fecha_form)
                    st.rerun()

    with tab2:
        df = get_data()
        if not df.empty:
            prs = df.sort_values('peso', ascending=False).drop_duplicates('ejercicio')
            for _, pr in prs.iterrows():
                st.markdown(f"""<div class="pr-card"><b>{pr['ejercicio']}</b><br>
                            <span style="font-size:1.5rem; color:#FF3D00;">{pr['peso']} kg</span></div>""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()