import streamlit as st
import yaml
from pyairtable import Api

# --- CARGAR USUARIOS AUTORIZADOS ---
try:
    with open('config.yaml') as file:
        config = yaml.safe_load(file)
    user_list = config['authorized_users']
except FileNotFoundError:
    st.error("Error: No se encontró el archivo 'config.yaml'. Asegúrate de que exista en la misma carpeta que 'app.py'.")
    st.stop()


# --- LÓGICA DE "LOGIN" CON MENÚ DESPLEGABLE ---

# Revisa si un usuario ya ha sido guardado en la sesión actual
if 'user' not in st.session_state or not st.session_state.user:
    st.title("Bienvenido al Inventario WCAR 🚚")
    st.write("---")

    # Muestra un menú para seleccionar el nombre. La primera opción está en blanco.
    selected_user = st.selectbox(
        "Para continuar, por favor selecciona tu nombre de la lista:",
        options=[""] + user_list
    )

    if st.button("Ingresar"):
        if selected_user:
            st.session_state.user = selected_user
            st.rerun() # Vuelve a cargar la página para mostrar la app principal
        else:
            st.warning("Debes seleccionar un nombre de la lista.")

else:
    # --- PANTALLA PRINCIPAL DE LA APLICACIÓN ---
    
    # Muestra quién está logueado y un botón para "cambiar de usuario"
    st.sidebar.write(f"Usuario actual: **{st.session_state.user}**")
    if st.sidebar.button("Cambiar de usuario"):
        del st.session_state.user # Borra el usuario de la memoria
        st.rerun() # Vuelve a cargar para mostrar el login de nuevo

    st.title('Inventario de Vehículos')
    st.write("---")

    # --- CONEXIÓN A AIRTABLE ---
    # Este código se ejecuta solo si el usuario ha seleccionado un nombre
    try:
        api = Api(st.secrets["AIRTABLE_TOKEN"])
        table = api.table(st.secrets["BASE_ID"], st.secrets["TABLE_NAME"])
    except Exception as e:
        st.error("Error de conexión con Airtable. Verifica los 'secrets' en Streamlit Cloud.")
        st.stop()
    
    # ======================================================================
    # AQUÍ VA TODO EL RESTO DE TU CÓDIGO
    # (El que muestra la tabla de vehículos, los filtros, etc.)
    # ======================================================================


    # --- EJEMPLO DE CÓMO USAR EL NOMBRE DEL USUARIO ---
    # Cuando vayas a actualizar un registro, harás esto:
    # 
    # id_del_carro = "recXXXXXXXX" # El ID del registro a cambiar
    # nueva_ubicacion = "Patio 3"
    #
    # campos_actualizados = {
    #     "UBICACION ACTUAL": nueva_ubicacion,
    #     "Modificado Por": st.session_state.user  # ¡Aquí guardamos el nombre!
    # }
    #
    # table.update(id_del_carro, campos_actualizados)
    # st.success(f"Ubicación actualizada por {st.session_state.user}.")