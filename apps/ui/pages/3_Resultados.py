import streamlit as st
from utils.api_client import get_status, download_zip, download_errors

st.set_page_config(page_title="Resultados", layout="centered")
st.title("3) Resultados")

batch_id = st.session_state.get("batch_id")
if not batch_id:
    st.warning("No hay batch_id. Ve a **Subir Lote**.")
    st.stop()

status = get_status(batch_id)
st.write(f"**Estado:** {status['status']}")
st.write(f"Total: {status['total']} | OK: {status['ok']} | Error: {status['error']}")

if status["status"] != "DONE":
    st.info("El lote aún no ha terminado. Ve a **Progreso**.")
    st.stop()

if st.button("Descargar ZIP (PDFs)"):
    content = download_zip(batch_id)
    st.download_button("Bajar salida.zip", data=content, file_name="salida.zip", mime="application/zip")

if status["error"] > 0:
    if st.button("Descargar errores.csv"):
        content = download_errors(batch_id)
        st.download_button("Bajar errores.csv", data=content, file_name="errores.csv", mime="text/csv")
