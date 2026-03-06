import streamlit as st

st.set_page_config(page_title="DocGen", layout="centered")
st.info("Los resultados se muestran en la pagina principal. Ve a **Home** en el menu lateral.")
st.page_link("Home.py", label="Ir a Home", icon="🏠")
