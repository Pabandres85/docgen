import streamlit as st

st.set_page_config(page_title="DocGen", layout="centered")

st.title("DocGen — Generación Masiva (Excel + Plantilla DOCX → PDFs + ZIP)")
st.markdown(
    """
Esta UI carga:
- **datos.xlsx**
- **plantilla.docx** con variables `{{NombreColumna}}` iguales al Excel

Luego ejecuta el lote vía API y descarga el **salida.zip** con un PDF por proceso.
"""
)

st.info("Ve a la página **Subir Lote** para iniciar.")
