// Convierte el HTML del DMSA a PDF A4 con número de página. Uso: node pdf.js dmsa.html salida.pdf
const path = require('path');
const { chromium } = require(process.env.PW || 'playwright');
(async () => {
  const [src, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(src), { waitUntil: 'networkidle' });
  await page.pdf({
    path: out, format: 'A4', printBackground: true,
    margin: { top: '16mm', bottom: '18mm', left: '15mm', right: '15mm' },
    displayHeaderFooter: true,
    headerTemplate: '<span></span>',
    footerTemplate: '<div style="font-size:8px;font-family:Inter,sans-serif;color:#7a8394;width:100%;padding:0 15mm;display:flex;justify-content:space-between"><span>DMSA · Asistente de Inteligencia de Precios · G. D\'Astolfo · Cohorte 2026</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
  });
  await browser.close();
})();
