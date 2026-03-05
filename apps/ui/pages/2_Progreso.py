import time

import streamlit as st

from utils.api_client import ApiClientError, get_status

st.set_page_config(page_title="Progreso", layout="centered")
st.title("2) Progreso")

batch_id = st.session_state.get("batch_id")
if not batch_id:
    st.warning("No hay batch_id. Ve a **Subir Lote**.")
    st.stop()

auto_refresh = st.checkbox("Auto actualizar (cada 2s)", value=True)
terminal_states = {"DONE", "DONE_WITH_ERRORS", "FAILED"}

try:
    status = get_status(batch_id)
except ApiClientError as e:
    st.error(str(e))
    st.stop()

state = status["status"]
st.write(f"**Batch:** {batch_id}")
st.write(f"**Estado:** {state}")
st.progress(float(status["progress"]))
st.write(f"Total: {status['total']} | OK: {status['ok']} | Error: {status['error']}")

if state == "DONE":
    st.success("Listo. Ve a la pagina **Resultados** para descargar.")
elif state == "DONE_WITH_ERRORS":
    st.warning("Proceso finalizado con errores. Ve a **Resultados**.")
elif state == "FAILED":
    st.error("El lote fallo antes de completarse. Revisa entradas e intenta de nuevo.")
elif auto_refresh:
    time.sleep(2)
    st.rerun()
