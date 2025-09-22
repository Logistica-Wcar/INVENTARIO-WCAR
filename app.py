# Importamos las librerías necesarias
import streamlit as st
import pandas as pd
from pyairtable import Api
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Gestor de Inventario wcar",
    page_icon="🚗",
    layout="wide"
)

# --- ESTILOS ---
st.markdown("""
<style>
    .stApp { background-color: #2E2E2E; }
    .title { font-size: 48px; font-weight: bold; color: #FFFFFF; text-align: center; }
    .subtitle { font-size: 24px; font-weight: bold; color: #FF6600; text-align: center; }
    .vehicle-card { background-color: #3C3C3C; padding: 20px; border-radius: 10px; border-left: 8px solid #FF6600; margin-bottom: 10px; }
    .label { color: #FFFFFF; font-weight: bold; font-size: 18px; }
    .value { color: #FF6600; font-size: 20px; font-weight: bold; }
    .stButton>button { background-color: #FF6600; color: #FFFFFF; border-radius: 5px; border: none; padding: 10px 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- CONEXIÓN A AIRTABLE ---
try:
    api = Api(st.secrets["AIRTABLE_TOKEN"])
    table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
except Exception as e:
    st.error("Error de conexión con Airtable. Verifica las llaves secretas en los ajustes de la aplicación.")
    st.stop()

# --- FUNCIONES PARA TRABAJAR CON AIRTABLE ---
@st.cache_data(ttl=30)
def load_data_from_airtable():
    all_records = table.all()
    records_list = [{'id': r['id'], **r['fields']} for r in all_records]
    df = pd.DataFrame(records_list)
    
    # Guardamos los nombres originales para usarlos al escribir datos
    st.session_state['original_columns'] = {col.upper(): col for col in df.columns}
    
    df.columns = df.columns.str.upper() # Estandarizamos para búsquedas
    return df

def update_location_in_airtable(record_id, field_name, new_location):
    try:
        table.update(record_id, {field_name: new_location})
        return True
    except Exception as e:
        st.error(f"No se pudo actualizar el registro: {e}")
        return False

# --- ENCABEZADO ---
st.image('Captura1.JPG', width=200)
st.markdown('<p class="subtitle">Gestor de Inventario wcar (Versión Multi-usuario en Tiempo Real)</p>', unsafe_allow_html=True)
st.markdown("---")

# --- CUERPO DE LA APP ---
inventario_df = load_data_from_airtable()
if 'change_log' not in st.session_state:
    st.session_state.change_log = []

if not inventario_df.empty:
    original_cols = st.session_state.get('original_columns', {})
    
    # Buscamos la columna de ubicación
    location_col_upper = None
    posibles_nombres = ['UBICACIÓN FÍSICA', 'UBICACION FISICA', 'UBICACIÓN ACTUAL', 'UBICACION ACTUAL', 'UBICACIÓN', 'UBICACION']
    for name in posibles_nombres:
        if name in inventario_df.columns:
            location_col_upper = name
            break
            
    st.header("Buscar y Actualizar Vehículo")
    placa_buscada = st.text_input("Ingresa la Placa a buscar:", max_chars=6).upper()

    if placa_buscada:
        vehiculo_encontrado = inventario_df[inventario_df['PLACA'] == placa_buscada]

        if not vehiculo_encontrado.empty and location_col_upper:
            info_vehiculo = vehiculo_encontrado.iloc[0]
            ubicacion_actual = info_vehiculo.get(location_col_upper, 'No definida')
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""<div class="vehicle-card"><p class="label">Placa:</p><p class="value">{info_vehiculo.get('PLACA', 'N/A')}</p></div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div class="vehicle-card"><p class="label">Ubicación Actual:</p><p class="value">{ubicacion_actual}</p></div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("Actualizar Ubicación")
            
            lista_ubicaciones = sorted(inventario_df[location_col_upper].dropna().unique().tolist())
            opciones_menu = ["Selecciona una opción..."] + lista_ubicaciones + ["Otra (Escribir nueva)"]
            seleccion_ubicacion = st.selectbox("Elige la nueva ubicación:", options=opciones_menu)
            
            nueva_ubicacion_final = ""
            if seleccion_ubicacion == "Otra (Escribir nueva)":
                nueva_ubicacion_final = st.text_input("Escribe el nombre de la nueva ubicación:")
            elif seleccion_ubicacion != "Selecciona una opción...":
                nueva_ubicacion_final = seleccion_ubicacion

            if st.button("Aplicar Cambio en Tiempo Real"):
                if nueva_ubicacion_final:
                    record_id = info_vehiculo.get('ID')
                    # CORRECCIÓN: Usamos el nombre original de la columna para escribir en Airtable
                    original_location_col_name = original_cols.get(location_col_upper)
                    
                    if update_location_in_airtable(record_id, original_location_col_name, nueva_ubicacion_final):
                        st.success(f"¡Éxito! La ubicación de {placa_buscada} se actualizó para todos los usuarios.")
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        st.session_state.change_log.append({
                            'Fecha y Hora': timestamp, 'Placa': placa_buscada,
                            'Ubicación Anterior': ubicacion_actual, 'Nueva Ubicación': nueva_ubicacion_final
                        })
                        st.info("El cambio se reflejará en todas las sesiones activas en unos segundos.")
                else:
                    st.warning("Por favor, selecciona o escribe una nueva ubicación.")
    
    st.markdown("---")
    st.header("Informe de Cambios de la Sesión Actual")
    if st.session_state.change_log:
        st.dataframe(pd.DataFrame(st.session_state.change_log))
