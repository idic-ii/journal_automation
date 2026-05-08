import asyncio
import os
import base64
from playwright.async_api import async_playwright

async def md_to_pdf(md_path, output_pdf_path, template_path):
    # 1. Read Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 2. Read Template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 3. Inject Markdown as Base64
    md_b64 = base64.b64encode(md_content.encode('utf-8')).decode('utf-8')
    injected_html = template.replace('MARKDOWN_B64_PLACEHOLDER', md_b64)

    temp_html_path = md_path + ".temp.html"
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(injected_html)

    # 4. Use Playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Load local file
        abs_html_path = os.path.abspath(temp_html_path)
        await page.goto(f"file:///{abs_html_path}")

        # Wait for rendering to complete
        await page.wait_for_function("window.rendered === true", timeout=60000)
        
        # Extra wait for mermaid font loading/rendering
        await asyncio.sleep(2)

        # Print to PDF
        await page.pdf(path=output_pdf_path, format="A4", 
            print_background=True,
            margin={
                "top": "15mm",
                "bottom": "15mm",
                "left": "15mm",
                "right": "15mm"
            }
        )

        await browser.close()

    # Clean up
    if os.path.exists(temp_html_path):
        os.remove(temp_html_path)

if __name__ == "__main__":
    MD_FILE = r"C:\Users\CAMONTOY\.gemini\antigravity\brain\4d0bd626-0b87-49f2-85a1-7a2e8218757f\informe_tecnico_proyecto.md"
    TEMPLATE = r"c:\Users\CAMONTOY\Desktop\proyectos_idic\automatizacion_revistas\scratch\pdf_template.html"
    OUTPUT = r"c:\Users\CAMONTOY\Desktop\proyectos_idic\automatizacion_revistas\informe_tecnico_completo.pdf"
    
    print(f"Convertiendo {MD_FILE} a PDF...")
    try:
        asyncio.run(md_to_pdf(MD_FILE, OUTPUT, TEMPLATE))
        print(f"Hecho! PDF guardado en: {OUTPUT}")
    except Exception as e:
        print(f"Error fatal: {e}")
