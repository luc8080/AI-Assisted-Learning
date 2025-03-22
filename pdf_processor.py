import pdfplumber

def extract_text_from_pdf(file):
    """使用 pdfplumber 解析 PDF 文字內容"""
    with pdfplumber.open(file) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    return text
