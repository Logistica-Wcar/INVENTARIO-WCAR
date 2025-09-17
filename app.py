# Importamos las librerías necesarias
import streamlit as st
import pandas as pd
import base64
from datetime import datetime # Necesario para registrar la fecha y hora del cambio

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Gestor de Inventario wcar",
    page_icon="🚗",
    layout="wide"
)

# --- ESTILOS Y COLORES CORPORATIVOS (CSS) ---
st.markdown("""
<style>
    /* Estilos (son los mismos que la versión anterior) */
    .stApp { background-color: #2E2E2E; }
    .title { font-size: 48px; font-weight: bold; color: #FFFFFF; text-align: center; }
    .subtitle { font-size: 24px; font-weight: bold; color: #FF6600; text-align: center; }
    .vehicle-card { background-color: #3C3C3C; padding: 20px; border-radius: 10px; border-left: 8px solid #FF6600; margin-bottom: 10px; }
    .label { color: #FFFFFF; font-weight: bold; font-size: 18px; }
    .value { color: #FF6600; font-size: 20px; font-weight: bold; }
    .stButton>button { background-color: #FF6600; color: #FFFFFF; border-radius: 5px; border: none; padding: 10px 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# --- FUNCIÓN PARA CARGAR DATOS ---
@st.cache_data(ttl=30)
def load_data_from_gsheet(gsheet_url):
    try:
        df = pd.read_csv(gsheet_url, encoding='utf-8')
        st.session_state['original_columns'] = list(df.columns)
        df.columns = df.columns.str.strip().str.upper()
        
        posibles_nombres_ubicacion = ['UBICACIÓN FÍSICA', 'UBICACION FISICA', 'UBICACIÓN ACTUAL', 'UBICACION ACTUAL', 'UBICACIÓN', 'UBICACION']
        location_column_name = None
        for name in posibles_nombres_ubicacion:
            if name in df.columns:
                location_column_name = name
                break 
        st.session_state['location_column'] = location_column_name

        for col in ['PLACA', 'MARCA', 'REFERENCIA']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        if 'AÑO' in df.columns:
            df['AÑO'] = pd.to_numeric(df['AÑO'], errors='coerce').fillna(0).astype(int)

        return df
    except Exception as e:
        st.error(f"Error al cargar los datos. Verifica el enlace CSV. Error: {e}")
        return None

# --- FUNCIÓN PARA CONVERTIR DATAFRAME A CSV ---
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# --- ENCABEZADO DE LA APLICACIÓN ---
try:
    st.image('Captura1.JPG', width=200)
except:
    st.markdown('<p class="title">wcar</p>', unsafe_allow_html=True)

st.markdown('<p class="subtitle">Gestor de Ubicación de Inventario (Versión Google Sheets)</p>', unsafe_allow_html=True)
st.markdown("---")

# --- CUERPO DE LA APLICACIÓN ---
st.header("1. Conecta tu Base de Datos")
gsheet_public_url = st.text_input("Pega aquí el enlace CSV de tu Google Sheet publicado:", placeholder="El enlace que copiaste en el Paso 1...")

if gsheet_public_url:
    if 'df' not in st.session_state:
        st.session_state.df = load_data_from_gsheet(gsheet_public_url)
    
    # INICIALIZAMOS EL REGISTRO DE CAMBIOS (EL INFORME)
    if 'change_log' not in st.session_state:
        st.session_state.change_log = []

    if st.session_state.df is not None:
        if 'PLACA' not in st.session_state.df.columns:
            st.error("¡Error Crítico! No se encontró una columna 'PLACA' en el archivo.")
        else:
            st.success("¡Conexión exitosa! Base de datos cargada.")
            location_col = st.session_state.get('location_column')
            
            # El diagnóstico ahora es opcional y está más limpio
            with st.expander("Ver diagnóstico de columnas"):
                st.write(st.session_state.get('original_columns', []))
                if location_col: st.info(f"✅ Columna de ubicación detectada: **'{location_col}'**")

            st.markdown("---")
            st.header("2. Busca y Actualiza el Vehículo")

            df_para_trabajar = st.session_state.df
            placa_buscada = st.text_input("Ingresa la Placa a buscar:", max_chars=6).upper()

            if placa_buscada:
                vehiculo_encontrado = df_para_trabajar[df_para_trabajar['PLACA'] == placa_buscada]

                if not vehiculo_encontrado.empty and location_col:
                    info_vehiculo = vehiculo_encontrado.iloc[0]
                    ubicacion_actual = info_vehiculo.get(location_col, 'No definida')
                    
                    # ... (código de visualización de tarjetas, sin cambios)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""<div class="vehicle-card"><p class="label">Placa:</p><p class="value">{info_vehiculo.get('PLACA', 'N/A')}</p><p class="label">Marca y Referencia:</p><p class="value">{info_vehiculo.get('MARCA', 'N/A')} {info_vehiculo.get('REFERENCIA', 'N/A')}</p></div>""", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""<div class="vehicle-card"><p class="label">Año:</p><p class="value">{info_vehiculo.get('AÑO', 'N/A')}</p><p class="label">Ubicación Actual:</p><p class="value">{ubicacion_actual}</p></div>""", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.subheader("Actualizar Ubicación")
                    
                    lista_ubicaciones = sorted(df_para_trabajar[location_col].dropna().unique().tolist())
                    opciones_menu = ["Selecciona una opción..."] + lista_ubicaciones + ["Otra (Escribir nueva)"]
                    seleccion_ubicacion = st.selectbox("Elige la nueva ubicación:", options=opciones_menu)
                    
                    nueva_ubicacion_final = ""
                    if seleccion_ubicacion == "Otra (Escribir nueva)":
                        nueva_ubicacion_final = st.text_input("Escribe el nombre de la nueva ubicación:")
                    elif seleccion_ubicacion != "Selecciona una opción...":
                        nueva_ubicacion_final = seleccion_ubicacion

                    if st.button("Aplicar Cambio"):
                        if nueva_ubicacion_final:
                            # GUARDAMOS EL CAMBIO EN EL REGISTRO
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.change_log.append({
                                'Fecha y Hora': timestamp,
                                'Placa': placa_buscada,
                                'Ubicación Anterior': ubicacion_actual,
                                'Nueva Ubicación': nueva_ubicacion_final
                            })
                            
                            # Actualizamos el DataFrame
                            st.session_state.df.loc[st.session_state.df['PLACA'] == placa_buscada, location_col] = nueva_ubicacion_final
                            st.success(f"Cambio para {placa_buscada} registrado. Descarga el inventario y el informe al finalizar.")
                        else:
                            st.warning("Por favor, selecciona o escribe una nueva ubicación.")

                    st.markdown("---")
                    st.header("3. Guarda los Cambios")
                    st.info("Descarga el inventario actualizado para subirlo a Google Sheets.")
                    csv_descargable = convert_df_to_csv(st.session_state.df)
                    st.download_button(
                        label="📥 Descargar Inventario Actualizado (.csv)",
                        data=csv_descargable,
                        file_name='inventario_wcar_actualizado.csv',
                        mime='text/csv',
                    )

                    # --- NUEVA SECCIÓN: INFORME DE CAMBIOS ---
                    st.markdown("---")
                    st.header("4. Informe de Cambios de la Sesión")
                    
                    if st.session_state.change_log:
                        log_df = pd.DataFrame(st.session_state.change_log)
                        st.dataframe(log_df) # Mostramos la tabla del informe
                        
                        # Creamos el botón para descargar el informe
                        log_csv = convert_df_to_csv(log_df)
                        st.download_button(
                            label="📥 Descargar Informe de Cambios (.csv)",
                            data=log_csv,
                            file_name='informe_cambios_wcar.csv',
                            mime='text/csv',
                        )
                    else:
                        st.info("Aún no se han realizado cambios en esta sesión.")

                # ... (código de manejo de errores, sin cambios)
                elif not vehiculo_encontrado.empty:
                     st.error("Se encontró el vehículo, pero no se pudo identificar la columna de ubicación.")
                else:
                    st.warning("No se encontró ningún vehículo con esa placa.")