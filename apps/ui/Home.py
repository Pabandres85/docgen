import io
import re
import time
import unicodedata

import pandas as pd
import streamlit as st


def _normalize_col(col: str) -> str:
    nfkd = unicodedata.normalize("NFKD", str(col))
    ascii_str = "".join(c for c in nfkd if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9_]", "_", ascii_str)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "col"

from utils.api_client import ApiClientError, create_batch, download_errors, download_zip, get_status, run_batch

st.set_page_config(page_title="DocGen", layout="centered")
st.title("DocGen — Excel + Plantilla DOCX → PDFs + ZIP")

# ── Init session state ────────────────────────────────────────────────────────
for key, default in [("phase", "upload"), ("batch_id", None), ("started_at", None), ("elapsed_done", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 1 — SUBIR Y CONFIGURAR
# ═══════════════════════════════════════════════════════════════════════════════
if st.session_state.phase == "upload":
    excel = st.file_uploader("Sube datos.xlsx", type=["xlsx"])
    template = st.file_uploader("Sube plantilla.docx", type=["docx"])

    cols = []
    if excel:
        try:
            raw_cols = list(pd.read_excel(io.BytesIO(excel.getvalue()), nrows=0, dtype=str).columns)
            cols = [_normalize_col(c) for c in raw_cols]
            st.info("Columnas disponibles (usar en Word y patron): " + "  ".join(f"`{c}`" for c in cols))
        except Exception:
            pass

    # Sugerir patron usando las primeras columnas utiles del Excel
    if cols:
        suggested = "_".join(f"{{{c}}}" for c in cols[:2])
    else:
        suggested = "registro_{row_index}"

    st.markdown("**Patron de nombre de archivo**")
    st.caption("Usa los nombres de columna entre llaves. Tambien existe `{row_index}`.")
    filename_pattern = st.text_input("filename_pattern", value=suggested)

    if st.button("Crear y ejecutar lote", type="primary", disabled=not (excel and template)):
        with st.spinner("Subiendo archivos..."):
            try:
                batch_id = create_batch(
                    excel_bytes=excel.getvalue(),
                    excel_name=excel.name,
                    template_bytes=template.getvalue(),
                    template_name=template.name,
                    filename_pattern=filename_pattern,
                )
            except ApiClientError as e:
                st.error(str(e))
                st.stop()

        with st.spinner("Iniciando procesamiento..."):
            try:
                run_batch(batch_id)
            except ApiClientError as e:
                st.error(str(e))
                st.stop()

        st.session_state.batch_id = batch_id
        st.session_state.started_at = time.time()
        st.session_state.elapsed_done = None
        st.session_state.phase = "running"
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 2 — PROCESANDO
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "running":
    batch_id = st.session_state.batch_id
    elapsed = time.time() - (st.session_state.started_at or time.time())

    try:
        status = get_status(batch_id)
    except ApiClientError as e:
        st.error(str(e))
        st.stop()

    state = status["status"]

    if state in {"DONE", "DONE_WITH_ERRORS", "FAILED"}:
        st.session_state.elapsed_done = elapsed
        st.session_state.phase = "done"
        st.rerun()

    # ── UI mientras procesa ──
    st.subheader("Procesando lote...")
    st.caption(f"Batch: `{batch_id}`")

    mins, secs = divmod(int(elapsed), 60)
    total = status["total"]
    ok = status["ok"]
    err = status["error"]
    progress = float(status["progress"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Tiempo", f"{mins:02d}:{secs:02d}")
    col2.metric("Total", total)
    col3.metric("OK", ok)
    col4.metric("Errores", err)

    st.progress(progress)

    if total == 0:
        st.caption("Iniciando worker... (puede tardar unos segundos en arrancar)")

    with st.spinner("Actualizando..."):
        time.sleep(2)
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# FASE 3 — RESULTADOS
# ═══════════════════════════════════════════════════════════════════════════════
elif st.session_state.phase == "done":
    batch_id = st.session_state.batch_id
    elapsed = st.session_state.elapsed_done or 0.0

    try:
        status = get_status(batch_id)
    except ApiClientError as e:
        st.error(str(e))
        st.stop()

    state = status["status"]
    total = status["total"]
    ok = status["ok"]
    err = status["error"]
    mins, secs = divmod(int(elapsed), 60)

    if state == "DONE":
        st.success(f"Lote completado en {mins:02d}:{secs:02d}")
    elif state == "DONE_WITH_ERRORS":
        st.warning(f"Lote finalizado con {err} error(s) — {mins:02d}:{secs:02d}")
    elif state == "FAILED":
        st.error("El lote fallo antes de completarse. Revisa las entradas e intenta de nuevo.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total", total)
    col2.metric("OK", ok)
    col3.metric("Errores", err)

    if state in {"DONE", "DONE_WITH_ERRORS"}:
        st.divider()
        try:
            zip_data = download_zip(batch_id)
            st.download_button(
                "Descargar salida.zip",
                data=zip_data,
                file_name="salida.zip",
                mime="application/zip",
                type="primary",
            )
        except ApiClientError as e:
            st.error(f"No se pudo obtener el ZIP: {e}")

        if err > 0:
            try:
                csv_data = download_errors(batch_id)
                st.download_button(
                    "Descargar errores.csv",
                    data=csv_data,
                    file_name="errores.csv",
                    mime="text/csv",
                )
            except ApiClientError as e:
                st.warning(f"No se pudo obtener errores.csv: {e}")

    st.divider()
    if st.button("Nuevo lote"):
        st.session_state.phase = "upload"
        st.session_state.batch_id = None
        st.session_state.started_at = None
        st.session_state.elapsed_done = None
        st.rerun()
