"""Genera el DMSA (HTML y PDF) a partir de datos.json y de los workflows exportados.

Uso: python3 build.py            -> dmsa.html
     node pdf.js dmsa.html salida.pdf   (requiere Playwright con Chromium)
"""
import json, pathlib
from jinja2 import Environment, FileSystemLoader

BASE = pathlib.Path(__file__).resolve().parent
WF = BASE.parent / 'workflows'


def num(x, dec=0):
    s = f"{x:,.{dec}f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def calcular_roi(p):
    horas_manual = p['consultas_mes'] * p['minutos_por_consulta'] / 60
    base = next(m for m in p['modelos'] if m.get('base'))
    modelos = []
    for m in p['modelos']:
        por_consulta = (p['tokens_entrada_por_consulta'] * m['entrada'] + p['tokens_salida_por_consulta'] * m['salida']) / 1e6
        modelos.append({**m, 'por_consulta': por_consulta, 'por_mes': por_consulta * p['consultas_mes'],
                        'por_mes_5000': por_consulta * 5000})
    costo_tokens = next(m for m in modelos if m.get('base'))['por_consulta']

    def escenario(vol, deriv=p['tasa_derivacion']):
        h_manual = vol * p['minutos_por_consulta'] / 60
        manual = h_manual * p['costo_hora_usd']
        h_resid = h_manual * deriv
        humano = h_resid * p['costo_hora_usd']
        tokens = vol * costo_tokens
        agente = humano + tokens + p['hosting_usd_mes']
        return {'vol': vol, 'h_manual': h_manual, 'manual': manual, 'h_resid': h_resid, 'humano': humano,
                'tokens': tokens, 'hosting': p['hosting_usd_mes'], 'agente': agente, 'ahorro': manual - agente,
                'h_evitadas': h_manual - h_resid}

    actual = escenario(p['consultas_mes'])
    payback = p['inversion_usd'] / actual['ahorro']
    roi12 = (actual['ahorro'] * 12 - p['inversion_usd']) / p['inversion_usd']
    sens = [dict(escenario(p['consultas_mes'], d), deriv=d) for d in (0.10, 0.25, 0.40)]
    for s in sens:
        s['payback'] = p['inversion_usd'] / s['ahorro']
    return {'p': p, 'horas_manual': horas_manual, 'modelos': modelos, 'base': base, 'actual': actual,
            'escalas': [escenario(v) for v in p['volumenes']], 'payback': payback, 'roi12': roi12,
            'sens': sens, 'ahorro_anual': actual['ahorro'] * 12}


def schema_compacto(sch):
    """JSON Schema legible en pocas líneas: una propiedad por línea."""
    props = ',\n'.join(f'  "{k}": {json.dumps(v, ensure_ascii=False)}' for k, v in sch['properties'].items())
    req = json.dumps(sch['required'], ensure_ascii=False)
    return '{\n "type": "object",\n "properties": {\n' + props + '\n },\n "required": ' + req + '\n}'


def contar_nodos(nombre):
    wf = json.loads((WF / nombre).read_text(encoding='utf-8'))
    nodos = [n for n in wf['nodes'] if not n['type'].endswith('stickyNote')]
    return len(nodos), len(wf['nodes']) - len(nodos)


def main():
    datos = json.loads((BASE / 'datos.json').read_text(encoding='utf-8'))
    umbral = json.loads((BASE / 'umbral_resultados.json').read_text(encoding='utf-8'))
    juez = json.loads((WF / 'PF_Juez_de_Calidad_Supervisor.json').read_text(encoding='utf-8'))
    schema = next(n for n in juez['nodes'] if n['name'] == 'Rúbrica JSON Schema')['parameters']['inputSchema']
    env = Environment(loader=FileSystemLoader(str(BASE)), autoescape=True)
    env.filters['num'] = num
    env.filters['pct'] = lambda x, dec=0: num(x * 100, dec) + '%'
    html = env.get_template('dmsa.html.j2').render(
        d=datos, r=calcular_roi(datos['roi']), umbral=umbral, schema=schema_compacto(json.loads(schema)),
        nodos_manager=contar_nodos('PF_Manager_Orquestador_Asincronico.json'))
    (BASE / 'dmsa.html').write_text(html, encoding='utf-8')
    print('dmsa.html generado')


if __name__ == '__main__':
    main()
