import re
from docx.shared import Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from .constants import ASJC

def log(msg):
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)

def fmt_issn(s):
    s = str(s).strip().replace("-", "")
    return f"{s[:4]}-{s[4:]}" if len(s) == 8 else s

def percentile_to_quartile(pct_str):
    try:
        p = float(pct_str)
        if p >= 75: return "Q1"
        if p >= 50: return "Q2"
        if p >= 25: return "Q3"
        return "Q4"
    except:
        return "N/A"

def get_asjc_names(code_str):
    code = str(code_str).strip()
    if code in ASJC:
        return ASJC[code]
    prefix = code[:2]
    if prefix in ASJC:
        return (ASJC[prefix][0], f"Subárea {code}")
    return (f"Código {code}", f"Subárea {code}")

def highlight_run(run):
    """Resalta un run (trozo de texto) en amarillo."""
    rPr = run._r.get_or_add_rPr()
    hl  = OxmlElement("w:highlight")
    hl.set(qn("w:val"), "yellow")
    rPr.append(hl)

def add_hyperlink(paragraph, url, text, font_name="Times New Roman", font_size_pt=11):
    """Agrega un hipervínculo con color RGB(0,0,255) y sin subrayado."""
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    hl_run = OxmlElement("w:r")
    rPr_hl = OxmlElement("w:rPr")
    
    rFonts_hl = OxmlElement("w:rFonts")
    rFonts_hl.set(qn("w:ascii"), font_name)
    rFonts_hl.set(qn("w:hAnsi"), font_name)
    rPr_hl.append(rFonts_hl)
    
    sz_hl = OxmlElement("w:sz")
    sz_hl.set(qn("w:val"), str(font_size_pt * 2))
    rPr_hl.append(sz_hl)
    
    color_hl = OxmlElement("w:color")
    color_hl.set(qn("w:val"), "0000FF")
    rPr_hl.append(color_hl)
    
    u_hl = OxmlElement("w:u")
    u_hl.set(qn("w:val"), "none")
    rPr_hl.append(u_hl)
    
    hl_run.append(rPr_hl)
    hl_text = OxmlElement("w:t")
    hl_text.set(qn("xml:space"), "preserve")
    hl_text.text = text
    hl_run.append(hl_text)
    hyperlink.append(hl_run)
    paragraph._p.append(hyperlink)

def add_image_border(doc):
    """Agrega borde de 1pt color #999999 a la última imagen insertada."""
    last_paragraph = doc.paragraphs[-1]
    inline_elements = last_paragraph._p.findall('.//' + qn('wp:inline'))
    if not inline_elements:
        inline_elements = last_paragraph._p.findall('.//' + qn('wp:anchor'))
    
    for inline in inline_elements:
        spPr = inline.find('.//' + qn('pic:spPr'))
        if spPr is None: continue
        ln = OxmlElement('a:ln')
        ln.set('w', '12700')  # 1pt
        solidFill = OxmlElement('a:solidFill')
        srgbClr = OxmlElement('a:srgbClr')
        srgbClr.set('val', '999999')
        solidFill.append(srgbClr)
        ln.append(solidFill)
        spPr.append(ln)
