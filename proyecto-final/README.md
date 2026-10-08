# Proyecto Final Integrador: Sistema Agéntico Empresarial

Asistente de Inteligencia de Precios: sistema agéntico asincrónico y supervisado en n8n
(patrón Manager-Worker, supervisor AI-as-a-Judge, aprobación humana y despacho por Gmail).

## Contenido

| Carpeta | Qué hay |
|---|---|
| `workflows/` | JSON importables de los 4 workflows "PF -" (sin credenciales; solo referencias por nombre) |
| `kit_pruebas/` | `PROBAR_SISTEMA.bat` + `probar_sistema.ps1`: corre las 6 pruebas contra el webhook de producción y guarda los resultados; `LEEME_PASOS.txt` con los pasos |
| `dmsa/` | Fuentes del informe (DMSA): plantilla, datos, diagramas y el script que calcula el ROI |

## Generar el PDF del DMSA

```bash
cd proyecto-final/dmsa
python3 build.py                     # dmsa.html a partir de datos.json y los workflows
node pdf.js dmsa.html DAstolfo_Gianfranco_ProyectoFinal_AI_Experto.pdf   # requiere Playwright
```

`render_lienzo.py` dibuja el lienzo de cada workflow a partir de su JSON.

## Cambios respecto de la primera versión de los workflows

- **Manager:** la cola de aprobación humana pasó de Telegram a Gmail (send-and-wait). Telegram
  rechaza botones que apuntan a `http://localhost` ("Wrong HTTP URL"), y el modo Markdown fallaba
  con nombres de criterios con guion bajo.
- **Manager y Alertas:** el texto variable de los avisos de Telegram se sanea; si el aviso falla,
  el error igual queda registrado en el log.
