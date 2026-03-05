import time
import streamlit as st
from utils.api_client import get_status

st.set_page_config(page_title="Progreso", layout="centered")
st.title("2) Progreso")

batch_id = st.session_state.get("batch_id")
if not batch_id:
    st.warning("No hay batch_id. Ve a **Subir Lote**.")
    st.stop()

placeholder = st.empty()

auto_refresh = st.checkbox("Auto actualizar (cada 2s)", value=True)

while True:
    status = get_status(batch_id)
    with placeholder.container():
        st.write(f"**Batch:** {batch_id}")
        st.write(f"**Estado:** {status['status']}")
        st.progress(float(status["progress"]))
        st.write(f"Total: {status['total']} | OK: {status['ok']} | Error: {status['error']}")
        if status["status"] == "DONE":
            st.success("Listo. Ve a la página **Resultados** para descargar.")
            break

    if not auto_refresh:
        break
    time.sleep(2)
