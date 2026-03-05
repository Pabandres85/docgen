import streamlit as st

from utils.api_client import ApiClientError, download_errors, download_zip, get_status

st.set_page_config(page_title="Resultados", layout="centered")
st.title("3) Resultados")

batch_id = st.session_state.get("batch_id")
if not batch_id:
    st.warning("No hay batch_id. Ve a **Subir Lote**.")
    st.stop()

try:
    status = get_status(batch_id)
except ApiClientError as e:
    st.error(str(e))
    st.stop()

state = status["status"]
st.write(f"**Estado:** {state}")
st.write(f"Total: {status['total']} | OK: {status['ok']} | Error: {status['error']}")

if state == "FAILED":
    st.error("No se pudo completar el lote. Vuelve a cargar y ejecutar.")
    st.stop()

if state not in {"DONE", "DONE_WITH_ERRORS"}:
    st.info("El lote aun no ha terminado. Ve a **Progreso**.")
    st.stop()

if st.button("Descargar ZIP (PDFs)"):
    try:
        content = download_zip(batch_id)
        st.download_button("Bajar salida.zip", data=content, file_name="salida.zip", mime="application/zip")
    except ApiClientError as e:
        st.error(str(e))

if status["error"] > 0 and st.button("Descargar errores.csv"):
    try:
        content = download_errors(batch_id)
        st.download_button("Bajar errores.csv", data=content, file_name="errores.csv", mime="text/csv")
    except ApiClientError as e:
        st.error(str(e))
