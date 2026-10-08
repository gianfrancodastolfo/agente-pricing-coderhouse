Necesito que completes las pruebas de mi proyecto final. Es un sistema en n8n 2.38.1 que corre en mi PC, en http://localhost:5678. Trabajá en pestañas nuevas y no copies ni muestres claves, tokens ni contraseñas. Si algo falla dos veces seguidas, pará y avisame qué pasó.

1. **Abrir n8n.** Abrí http://localhost:5678. Si pide usuario y contraseña, pedímelos a mí.

2. **Renovar credenciales.** Overview → Credentials → "Google Sheets account" → "Switch account" (o "Reconnect") → elegí la cuenta gianfrancodastolfo@gmail.com → Permitir → Save. Repetí lo mismo con "Gmail account". Si Google pide una confirmación que solo puedo dar yo, avisame y esperá.

3. **Actualizar el Manager.**
   - Abrí el workflow "PF - Manager Orquestador Asincrónico".
   - Hacé clic en un espacio vacío del lienzo, apretá Ctrl+A y después Supr.
   - En el menú "..." (arriba a la derecha) elegí "Import from URL..." y pegá esta URL:
     `https://raw.githubusercontent.com/gianfrancodastolfo/agente-pricing-coderhouse/main/proyecto-final/workflows/PF_Manager_Orquestador_Asincronico.json`
   - Verificá:
     - Que haya unos 26 nodos y 5 notas de color.
     - Que el nodo "Cola de Aprobación Humana (Gmail)" tenga la credencial "Gmail account".
     - Que los nodos de Google Sheets tengan "Google Sheets account".
   - Guardá con Ctrl+S y tocá "Publish".

4. **Cargar la base de conocimiento.** Abrí "Worker 1 - Consulta de Datos" y tocá "Execute workflow" (la rama "When clicking 'Execute workflow'"). Esperá que todo quede en verde.

5. **Correr las 6 pruebas.**
   - Abrí una pestaña NUEVA en http://localhost:5678 y no la uses para nada más.
   - En esa pestaña ejecutá este JavaScript. Corre en segundo plano unos 5 minutos:

```js
(async () => {
  const url = '/webhook/agente-pricing';
  const run = new Date().toISOString().slice(5, 16).replace(/[-T:]/g, '');
  const q1 = '¿Cuál es el precio oferta y el stock actual del Smartwatch FitPulse 3 (SKU ELEC-002)?';
  const pruebas = [
    ['PF-' + run + '-001', 'demo-ventas-01', q1],
    ['PF-' + run + '-002', 'demo-ventas-01', 'Un cliente mayorista pide un 30% de descuento en Indumentaria, ¿se puede aprobar?'],
    ['PF-' + run + '-003', 'demo-soporte-02', '¿Cuál es el procedimiento para tramitar el reembolso de viáticos de un viaje corporativo del equipo de Sales Ops?'],
    ['PF-' + run + '-004', 'demo-ventas-03', 'Un cliente pide 40% de descuento en la notebook ELEC-005, ¿se lo puedo dar?'],
    ['PF-' + run + '-001', 'demo-ventas-01', q1],
    ['PF-' + run + '-006', 'demo-ventas-01', ''],
  ];
  window.__pf = { run, estado: 'corriendo', resultados: [] };
  for (let i = 0; i < pruebas.length; i++) {
    const [requestId, sessionId, consulta] = pruebas[i];
    const t0 = performance.now();
    let http = 0, respuesta = '';
    try {
      const r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ requestId, sessionId, canal: 'webhook', consulta }) });
      http = r.status; respuesta = await r.text();
    } catch (e) { respuesta = String(e); }
    window.__pf.resultados.push({ prueba: i + 1, requestId, http, ms: Math.round(performance.now() - t0), respuesta });
    if (http === 500 || http === 404) { window.__pf.estado = 'cortado: HTTP ' + http; return; }
    if (i < 3) await new Promise(res => setTimeout(res, 75000));
  }
  window.__pf.estado = 'terminado';
})();
```

   - Esperá unos 5 minutos y leé el resultado en esa misma pestaña con `JSON.stringify(window.__pf)`.
   - Si el estado dice "cortado: HTTP 500", lo más probable es que las credenciales de Google sigan vencidas: volvé al paso 2.
   - Si dice "cortado: HTTP 404", el Manager no está publicado: volvé al paso 3.

6. **Revisión humana.**
   - Abrí Gmail y buscá los mails con asunto "[Agente de Pricing] Revisión humana requerida".
   - En el primero tocá "Aprobar y enviar". Si hay un segundo, tocá "Descartar".
   - Se abre una pestaña de localhost:5678 que confirma la acción.
   - Si todavía no llegó ninguno, esperá 2 minutos y volvé a buscar.

7. **Al terminar**, mostrame el texto completo de `JSON.stringify(window.__pf)` para que lo copie.
