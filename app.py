import streamlit as st
import yaml
from pyairtable import Api

# --- CARGAR USUARIOS AUTORIZADOS ---
# (Esta parte se queda exactamente igual)
try:
    with open('config.yaml') as file:
        config = yaml.safe_load(file)
    user_list = config['authorized_users']
except FileNotFoundError:
    st.error("Error: No se encontró el archivo 'config.yaml'. Asegúrate de que exista.")
    st.stop()


# --- LÓGICA DE "LOGIN" CON MENÚ DESPLEGABLE ---
# (Esta parte también se queda igual)
if 'user' not in st.session_state or not st.session_state.user:
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

# --- PANTALLA PRINCIPAL DE LA APLICACIÓN (CUANDO EL USUARIO YA INGRESÓ) ---
else:
    # Muestra quién está logueado y un botón para "cambiar de usuario"
    # (Esto se mostrará en todas las páginas)
    st.sidebar.write(f"Usuario actual: **{st.session_state.user}**")
    if st.sidebar.button("Cambiar de usuario"):
        del st.session_state.user
        st.rerun()

    # --- MENÚ DE NAVEGACIÓN ---
    # (¡AQUÍ ESTÁ LA MAGIA! Creamos el menú en la barra lateral)
    pagina_seleccionada = st.sidebar.radio(
        "Menú Principal",
        ["Inventario de Vehículos", "Administrar Usuarios"]
    )
    st.sidebar.write("---") # Una línea para separar

    # --- CONEXIÓN A AIRTABLE ---
    # (La conexión se hace aquí una sola vez)
    try:
        api = Api(st.secrets["AIRTABLE_TOKEN"])
        table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
    except Exception as e:
        st.error("Error de conexión con Airtable. Verifica los 'secrets' en Streamlit Cloud.")
        st.stop()

    # --- SECCIÓN 1: INVENTARIO DE VEHÍCULOS ---
    if pagina_seleccionada == "Inventario de Vehículos":
        st.title('🗺️ Inventario de Vehículos')
        st.write("---")

        # ======================================================================
        # AQUÍ DEBES PEGAR TODO TU CÓDIGO ANTIGUO
        # (El que usabas para buscar el vehículo, el menú desplegable para
        # cambiar la ubicación, el botón de aplicar cambios y el historial).
        # ======================================================================
        
        st.info("Aquí va la funcionalidad del mapa de vehículos.") # Línea temporal


    # --- SECCIÓN 2: ADMINISTRAR USUARIOS ---
    elif pagina_seleccionada == "Administrar Usuarios":
        st.title('👤 Administración de Usuarios')
        st.write("---")

        # ======================================================================
        # AQUÍ VA EL NUEVO CÓDIGO PARA MOSTRAR LA LISTA DE USUARIOS
        # ======================================================================

        # Ejemplo de cómo mostrar los datos de la tabla:
        st.write("A continuación se muestra la lista de usuarios:")
        try:
            # Pide todos los registros a Airtable
            todos_los_registros = table.all()
            
            # Convierte los datos a un formato que Streamlit entiende mejor
            # (una lista de diccionarios)
            datos_para_mostrar = [registro['fields'] for registro in todos_los_registros]
            
            # Muestra la tabla en la página
            st.dataframe(datos_para_mostrar, use_container_width=True)

        except Exception as e:
            st.error(f"No se pudo cargar la información de Airtable: {e}")
