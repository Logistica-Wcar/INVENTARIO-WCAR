# ===================================================================
# PARTE 1: IMPORTACIONES Y CONFIGURACIÓN INICIAL
# ===================================================================
import streamlit as st
import pandas as pd
import yaml
from pyairtable import Api, Table
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

# --- CARGAR USUARIOS AUTORIZADOS PARA EL LOGIN ---
try:
    with open('config.yaml') as file:
        config = yaml.safe_load(file)
    user_list = config['authorized_users']
except FileNotFoundError:
    st.error("Error: No se encontró el archivo 'config.yaml'.")
    st.stop()


# ===================================================================
# PARTE 2: LÓGICA DE LOGIN
# ===================================================================
if 'user' not in st.session_state or not st.session_state.user:
    st.image('Captura1.JPG', width=200)
    st.title("Bienvenido al Inventario WCAR 🚚")
    st.write("---")
    selected_user = st.selectbox(
        "Para continuar, por favor selecciona tu nombre de la lista:",
        options=[""] + user_list
    )
    if st.button("Ingresar"):
        if selected_user:
            st.session_state.user = selected_user
            st.rerun()
        else:
            st.warning("Debes seleccionar un nombre de la lista.")

# ===================================================================
# PARTE 3: APLICACIÓN PRINCIPAL (SI EL LOGIN FUE EXITOSO)
# ===================================================================
else:
    # --- CONEXIÓN A AIRTABLE ---
    try:
        api = Api(st.secrets["AIRTABLE_TOKEN"])
        table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
    except Exception as e:
        st.error("Error de conexión con Airtable. Verifica los 'secrets' en Streamlit Cloud.")
        st.stop()

    # --- FUNCIONES PARA MANEJAR DATOS ---
    @st.cache_data(ttl=30)
    def load_data_from_airtable():
        # --- ¡AQUÍ ESTÁ LA CORRECCIÓN CRÍTICA! ---
        # Le decimos a la función que lea los datos desde nuestra nueva vista sin filtros.
        all_records = table.all(view="API_View")
        records_list = [{'id': r['id'], **r['fields']} for r in all_records]
        df = pd.DataFrame(records_list)
        df.columns = df.columns.str.upper()
        return df

    def update_location_in_airtable(record_id, field_name, new_location, user_name):
        try:
            # Actualizamos la ubicación Y también quién la modificó
            fields_to_update = {
                field_name: new_location,
                'Modificado Por': user_name,
                'Fecha Modificacion': datetime.now().isoformat()
            }
            table.update(record_id, fields_to_update)
            return True
        except Exception as e:
            st.error(f"No se pudo actualizar el registro: {e}")
            return False

    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.image('Captura1.JPG', width=100)
    st.sidebar.write(f"Usuario: **{st.session_state.user}**")
    if st.sidebar.button("Cambiar de usuario"):
        del st.session_state.user
        st.rerun()
    st.sidebar.markdown("---")
    
    # --- AQUÍ CREAMOS EL MENÚ DE NAVEGACIÓN ---
    pagina_seleccionada = st.sidebar.radio(
        "Menú Principal",
        ["Inventario de Vehículos", "Listado de Usuarios"]
    )

    # --- SECCIÓN 1: PÁGINA DEL INVENTARIO DE VEHÍCULOS ---
    if pagina_seleccionada == "Inventario de Vehículos":
        
        # --- ESTE ES TODO TU CÓDIGO ANTIGUO DEL INVENTARIO, YA INTEGRADO ---
        st.markdown('<p class="subtitle">Gestor de Inventario (Versión Multi-usuario en Tiempo Real)</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        inventario_df = load_data_from_airtable()
        if 'change_log' not in st.session_state:
            st.session_state.change_log = []

        if not inventario_df.empty:
            location_col_name_upper = next((name for name in ['UBICACIÓN FÍSICA', 'UBICACION FISICA', 'UBICACIÓN ACTUAL', 'UBICACION ACTUAL', 'UBICACIÓN', 'UBICACION'] if name in inventario_df.columns), None)
            
            st.header("Buscar y Actualizar Vehículo")
            placa_buscada = st.text_input("Ingresa la Placa a buscar:", max_chars=6).upper()

            if placa_buscada:
                vehiculo_encontrado = inventario_df[inventario_df['PLACA'] == placa_buscada]
                if not vehiculo_encontrado.empty and location_col_name_upper:
                    info_vehiculo = vehiculo_encontrado.iloc[0]
                    ubicacion_actual = info_vehiculo.get(location_col_name_upper, 'No definida')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""<div class="vehicle-card"><p class="label">Placa:</p><p class="value">{info_vehiculo.get('PLACA', 'N/A')}</p></div>""", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""<div class="vehicle-card"><p class="label">Ubicación Actual:</p><p class="value">{ubicacion_actual}</p></div>""", unsafe_allow_html=True)

                    st.markdown("---")
                    st.subheader("Actualizar Ubicación")
                    
                    lista_ubicaciones = sorted(inventario_df[location_col_name_upper].dropna().unique().tolist())
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
                            if update_location_in_airtable(record_id, location_col_name_upper, nueva_ubicacion_final, st.session_state.user):
                                st.success(f"¡Éxito! La ubicación de {placa_buscada} se actualizó.")
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                st.session_state.change_log.append({
                                    'Fecha y Hora': timestamp, 'Placa': placa_buscada,
                                    'Ubicación Anterior': ubicacion_actual, 'Nueva Ubicación': nueva_ubicacion_final,
                                    'Usuario': st.session_state.user
                                })
                                st.info("La información se refrescará en 30 segundos.")
                        else:
                            st.warning("Por favor, selecciona o escribe una nueva ubicación.")
            
            st.markdown("---")
            st.header("Informe de Cambios de la Sesión Actual")
            if st.session_state.change_log:
                st.dataframe(pd.DataFrame(st.session_state.change_log))
            else:
                st.info("Aún no se han realizado cambios en esta sesión.")

    # --- SECCIÓN 2: PÁGINA DEL LISTADO DE USUARIOS ---
    elif pagina_seleccionada == "Listado de Usuarios":
        st.header("👤 Listado General de la Base de Datos")
        st.write("Aquí se muestra toda la información registrada en Airtable.")
        
        try:
            df_completo = load_data_from_airtable()
            # Mostramos el DataFrame sin la columna 'id' que es interna de Airtable
            if 'ID' in df_completo.columns:
                df_completo = df_completo.drop(columns=['ID'])
            st.dataframe(df_completo, use_container_width=True)
        except Exception as e:
            st.error(f"No se pudo cargar la información: {e}")

