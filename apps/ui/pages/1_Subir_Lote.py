import streamlit as st
from utils.api_client import create_batch, run_batch

st.set_page_config(page_title="Subir lote", layout="centered")
st.title("1) Subir lote")

excel = st.file_uploader("Sube datos.xlsx", type=["xlsx"])
template = st.file_uploader("Sube plantilla.docx", type=["docx"])

st.markdown("### Patrón de nombre de archivo")
st.caption("Usa formato Python con llaves, p.ej: `Proceso_{NumeroProceso}_{NombreContribuyente}`. También existe `{row_index}`.")
filename_pattern = st.text_input("filename_pattern", value="Proceso_{NumeroProceso}_{NombreContribuyente}")

if "batch_id" not in st.session_state:
    st.session_state.batch_id = None

if st.button("Crear lote"):
    if not excel or not template:
        st.error("Debes subir Excel y plantilla DOCX.")
    else:
        batch_id = create_batch(
            excel_bytes=excel.getvalue(),
            excel_name=excel.name,
            template_bytes=template.getvalue(),
            template_name=template.name,
            filename_pattern=filename_pattern,
        )
        st.session_state.batch_id = batch_id
        st.success(f"Lote creado: {batch_id}")

if st.session_state.batch_id:
    st.divider()
    st.subheader("Ejecutar")
    if st.button("Procesar lote"):
        run_batch(st.session_state.batch_id)
        st.success("Procesamiento iniciado. Ve a la página **Progreso**.")
