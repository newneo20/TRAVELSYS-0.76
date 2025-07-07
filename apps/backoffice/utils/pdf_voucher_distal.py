# utils/pdf_voucher_distal.py

import asyncio
from playwright.async_api import async_playwright

async def generar_voucher_pdf_distal(reserva_id, url, output_path):
    print(f"⚙️ Iniciando generación de PDF para reserva ID {reserva_id}")
    print(f"🌐 URL del voucher: {url}")
    print(f"📂 Ruta de salida del PDF: {output_path}")

    async with async_playwright() as p:
        print("🚀 Lanzando navegador Chromium en modo headless...")
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print("⏳ Cargando la página del voucher...")
        await page.goto(url, wait_until='networkidle')

        print("🖨️ Generando PDF...")
        await page.pdf(path=output_path, format='A4', print_background=True)

        await browser.close()
        print("✅ PDF generado exitosamente y navegador cerrado.")
