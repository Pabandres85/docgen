from docxtpl import DocxTemplate

def render_docx(template_path: str, context: dict, out_docx_path: str) -> None:
    doc = DocxTemplate(template_path)
    doc.render(context)
    doc.save(out_docx_path)
