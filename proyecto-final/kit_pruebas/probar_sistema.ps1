# Kit de pruebas - Proyecto Final (Agente de Inteligencia de Precios)
# Corre las 6 pruebas contra el webhook de PRODUCCION de n8n, mide los tiempos
# de respuesta y deja los resultados en un .txt y en el portapapeles.

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$Base  = 'http://localhost:5678'
$Url   = "$Base/webhook/agente-pricing"
$Run   = Get-Date -Format 'MMdd-HHmm'
$Pausa = 75   # segundos entre consultas que usan IA (cuida el cupo gratuito de Gemini)

function Enviar([string]$json) {
  $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    $r = Invoke-WebRequest -Uri $Url -Method Post -Body $bytes -ContentType 'application/json; charset=utf-8' -UseBasicParsing -TimeoutSec 120
    $sw.Stop()
    return [pscustomobject]@{ code = [int]$r.StatusCode; ms = $sw.ElapsedMilliseconds; body = [string]$r.Content }
  } catch {
    $sw.Stop()
    $code = 0
    try { $code = [int]$_.Exception.Response.StatusCode } catch {}
    $body = if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { $_.Exception.Message }
    return [pscustomobject]@{ code = $code; ms = $sw.ElapsedMilliseconds; body = [string]$body }
  }
}

function Cuerpo($id, $sesion, $consulta) {
  return '{"requestId":"' + $id + '","sessionId":"' + $sesion + '","canal":"webhook","consulta":"' + $consulta + '"}'
}

Write-Host ''
Write-Host '=== Kit de pruebas - Agente de Inteligencia de Precios ===' -ForegroundColor Cyan
Write-Host "Corrida: $Run"
Write-Host ''

# 0) n8n tiene que estar abierto
try {
  Invoke-WebRequest -Uri "$Base/healthz" -UseBasicParsing -TimeoutSec 10 | Out-Null
} catch {
  Write-Host 'n8n no responde en http://localhost:5678. Abrí n8n, esperá a que cargue y volvé a ejecutar este archivo.' -ForegroundColor Red
  exit 1
}

# Las consultas van con escapes \uXXXX para que los acentos lleguen bien en cualquier Windows.
$pruebas = @(
  @{ n = '1'; id = "PF-$Run-001"; sesion = 'demo-ventas-01';
     consulta = '¿Cuál es el precio oferta y el stock actual del Smartwatch FitPulse 3 (SKU ELEC-002)?' },
  @{ n = '2'; id = "PF-$Run-002"; sesion = 'demo-ventas-01';
     consulta = 'Un cliente mayorista pide un 30% de descuento en Indumentaria, ¿se puede aprobar?' },
  @{ n = '3'; id = "PF-$Run-003"; sesion = 'demo-soporte-02';
     consulta = '¿Cuál es el procedimiento para tramitar el reembolso de viáticos de un viaje corporativo del equipo de Sales Ops?' },
  @{ n = '4'; id = "PF-$Run-004"; sesion = 'demo-ventas-03';
     consulta = 'Un cliente pide 40% de descuento en la notebook ELEC-005, ¿se lo puedo dar?' }
)

$res = @()
$i = 0
foreach ($p in $pruebas) {
  $i++
  Write-Host "Prueba $($p.n) ($($p.id))... " -NoNewline
  $r = Enviar (Cuerpo $p.id $p.sesion $p.consulta)
  Write-Host "HTTP $($r.code) en $($r.ms) ms"
  $res += [pscustomobject]@{ prueba = $p.n; requestId = $p.id; http = $r.code; ms = $r.ms; respuesta = $r.body }
  if ($r.code -eq 500 -or $r.code -eq 0) {
    Write-Host ''
    Write-Host 'El sistema devolvió un error antes de responder. Lo más probable: las credenciales de Google' -ForegroundColor Red
    Write-Host 'están vencidas. Renovalas (Credentials > Google Sheets account / Gmail account > Switch account > Save)' -ForegroundColor Red
    Write-Host 'y volvé a ejecutar este archivo.' -ForegroundColor Red
    break
  }
  if ($r.code -eq 404) {
    Write-Host 'El webhook no está registrado: el workflow "PF - Manager Orquestador Asincrónico" no está publicado.' -ForegroundColor Red
    break
  }
  if ($i -lt $pruebas.Count) {
    Write-Host "   esperando $Pausa s para la próxima consulta (procesamiento en segundo plano)..."
    Start-Sleep -Seconds $Pausa
  }
}

$ok = ($res.Count -eq 4) -and (($res | Where-Object { $_.http -ne 202 }).Count -eq 0)
if ($ok) {
  Write-Host "Prueba 5 (reenvío de PF-$Run-001: idempotencia)... " -NoNewline
  $r = Enviar (Cuerpo "PF-$Run-001" 'demo-ventas-01' $pruebas[0].consulta)
  Write-Host "HTTP $($r.code) en $($r.ms) ms"
  $res += [pscustomobject]@{ prueba = '5'; requestId = "PF-$Run-001"; http = $r.code; ms = $r.ms; respuesta = $r.body }

  Write-Host "Prueba 6 (consulta vacía)... " -NoNewline
  $r = Enviar (Cuerpo "PF-$Run-006" 'demo-ventas-01' '')
  Write-Host "HTTP $($r.code) en $($r.ms) ms"
  $res += [pscustomobject]@{ prueba = '6'; requestId = "PF-$Run-006"; http = $r.code; ms = $r.ms; respuesta = $r.body }

  Write-Host '   esperando 60 s para que termine la última consulta en segundo plano...'
  Start-Sleep -Seconds 60
}

$texto = "RESULTADOS KIT DE PRUEBAS - corrida $Run - " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz') + "`r`n"
$texto += ($res | ConvertTo-Json -Depth 4)
$archivo = Join-Path $PSScriptRoot "resultados_pruebas_$Run.txt"
[System.IO.File]::WriteAllText($archivo, $texto, (New-Object System.Text.UTF8Encoding($false)))
try { Set-Clipboard -Value $texto } catch {}

Write-Host ''
Write-Host '=== Listo ===' -ForegroundColor Green
Write-Host "Resultados guardados en: $archivo (y copiados al portapapeles)."
Write-Host ''
Write-Host 'Qué falta:' -ForegroundColor Yellow
Write-Host ' 1) Si te llegó un mail "Revisión humana requerida", abrilo EN ESTA PC y tocá "Aprobar y enviar" o "Descartar".'
Write-Host ' 2) Volvé al chat con Claude, escribí "listo" y pegá (Ctrl+V) los resultados.'
