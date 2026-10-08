"""Dibuja el lienzo de un workflow de n8n (SVG) a partir de su exportación JSON.

Respeta las posiciones, nombres, notas y conexiones reales del workflow; es una
representación fiel de la estructura, no una captura de pantalla de la app.
Uso: python3 render_lienzo.py workflow.json salida.svg [x0 y0 x1 y1]
"""
import json, sys, html, re, textwrap

STICKY = {1: '#fff5d6', 2: '#fde6d2', 3: '#fbe1e1', 4: '#e3f3e0', 5: '#dcecfb', 6: '#ebe5fd', 7: '#f0f0f0'}
STICKY_BORDER = {1: '#f0d68a', 2: '#f2b98f', 3: '#efb4b4', 4: '#a9d6a2', 5: '#9fc7ef', 6: '#c4b6f3', 7: '#cfcfcf'}
ICON = {  # tipo -> (glifo, color)
    'webhook': ('⚡', '#e8590c'), 'set': ('✎', '#4c6ef5'), 'if': ('IF', '#2f9e44'),
    'respondToWebhook': ('↩', '#495057'), 'googleSheets': ('▦', '#2b8a3e'), 'executeWorkflow': ('⇢', '#5f3dc4'),
    'switch': ('⇶', '#2f9e44'), 'telegram': ('✈', '#1c7ed6'), 'gmail': ('✉', '#c92a2a'), 'noOp': ('→', '#868e96'),
    'code': ('{ }', '#e67700'), 'errorTrigger': ('⚠', '#c92a2a'), 'executeWorkflowTrigger': ('▶', '#5f3dc4'),
    'agent': ('AI', '#5f3dc4'), 'lmChatGoogleGemini': ('G', '#1c7ed6'), 'outputParserStructured': ('{}', '#5f3dc4'),
}
TRIGGERS = {'webhook', 'errorTrigger', 'executeWorkflowTrigger'}
SUBNODES = {'lmChatGoogleGemini', 'outputParserStructured'}

def esc(s): return html.escape(str(s), quote=True)

def node_box(n):
    t = n['type'].split('.')[-1]
    x, y = n['position']
    if t in SUBNODES: return x, y, 80, 80
    if t == 'agent': return x, y, 200, 100
    return x, y, 100, 100

def outputs_of(n):
    t = n['type'].split('.')[-1]
    p = n.get('parameters', {})
    labels = []
    if t == 'if': labels = ['true', 'false']
    elif t == 'switch': labels = [r.get('outputKey', str(i)) for i, r in enumerate(p.get('rules', {}).get('values', []))]
    elif t == 'gmail' and p.get('operation') == 'sendAndWait': labels = ['']
    else: labels = ['']
    if n.get('onError') == 'continueErrorOutput': labels = labels + ['error']
    return labels

def wrap_name(name, width=16):
    return textwrap.wrap(name, width) or [name]

def render(wf, view=None, pad=60):
    nodes = {n['name']: n for n in wf['nodes']}
    stickies = [n for n in wf['nodes'] if n['type'].endswith('stickyNote')]
    real = [n for n in wf['nodes'] if not n['type'].endswith('stickyNote')]
    if view:
        x0, y0, x1, y1 = view
    else:
        xs, ys = [], []
        for n in real:
            x, y, w, h = node_box(n); xs += [x, x + w]; ys += [y, y + h + 60]
        for s in stickies:
            x, y = s['position']; p = s['parameters']; xs += [x, x + p.get('width', 240)]; ys += [y, y + p.get('height', 160)]
        x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    W, H = x1 - x0, y1 - y0
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="{x0} {y0} {W} {H}" font-family="Inter, DejaVu Sans, sans-serif">',
           '<defs><pattern id="dots" width="20" height="20" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="1" fill="#d5d8de"/></pattern>'
           '<marker id="m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#8a8f98"/></marker>'
           '<marker id="me" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#e03131"/></marker></defs>',
           f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="#f7f8fa"/><rect x="{x0}" y="{y0}" width="{W}" height="{H}" fill="url(#dots)"/>']
    # notas
    for s in stickies:
        x, y = s['position']; p = s['parameters']; w, h = p.get('width', 240), p.get('height', 160); c = p.get('color', 1)
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{STICKY.get(c, "#fff5d6")}" stroke="{STICKY_BORDER.get(c, "#f0d68a")}" stroke-width="1.5"/>')
        lines = p.get('content', '').split('\n')
        ty = y + 34
        for ln in lines:
            bold = ln.startswith('#')
            txt = re.sub(r'[#*]', '', ln).strip()
            if not txt: continue
            size = 22 if bold else 15
            for part in textwrap.wrap(txt, max(20, int(w / (size * 0.55)))):
                out.append(f'<text x="{x + 16}" y="{ty}" font-size="{size}" font-weight="{700 if bold else 400}" fill="#2b2b2b">{esc(part)}</text>')
                ty += size + 7
            ty += 4
    # conexiones
    for src, c in wf['connections'].items():
        if src not in nodes: continue
        sn = nodes[src]; sx, sy, sw, shh = node_box(sn); labels = outputs_of(sn)
        for typ, outs in c.items():
            for i, targets in enumerate(outs):
                for t in targets or []:
                    tn = nodes.get(t['node'])
                    if not tn: continue
                    tx, ty_, tw, th = node_box(tn)
                    if typ != 'main':  # sub-nodo IA: línea punteada hacia arriba
                        ax, ay = sx + sw / 2, sy; bx, by = tx + tw / 2, ty_ + th + (20 + 16 * len(wrap_name(tn['name'], 30)) if tn['type'].endswith('agent') else 0)
                        out.append(f'<path d="M{ax},{ay} C{ax},{ay - 40} {bx},{by + 40} {bx},{by}" fill="none" stroke="#8a8f98" stroke-width="2" stroke-dasharray="6 5"/>')
                        continue
                    n_out = len(labels)
                    ay = sy + shh * (i + 1) / (n_out + 1); ax = sx + sw
                    bx, by = tx, ty_ + th / 2
                    is_err = labels[i] == 'error' if i < len(labels) else False
                    col = '#e03131' if is_err else '#8a8f98'
                    dx = max(60, abs(bx - ax) / 2)
                    if bx < ax:  # conexión hacia atrás
                        mid = max(sy + shh, ty_ + th) + 50
                        d = f'M{ax},{ay} C{ax + 60},{ay} {ax + 60},{mid} {ax},{mid} L{bx},{mid} C{bx - 60},{mid} {bx - 60},{by} {bx},{by}'
                    else:
                        d = f'M{ax},{ay} C{ax + dx},{ay} {bx - dx},{by} {bx - 4},{by}'
                    out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2.2" marker-end="url(#{"me" if is_err else "m"})"/>')
    # nodos
    for n in real:
        t = n['type'].split('.')[-1]; x, y, w, h = node_box(n)
        glyph, col = ICON.get(t, ('•', '#495057'))
        if t in SUBNODES:
            out.append(f'<circle cx="{x + w / 2}" cy="{y + h / 2}" r="{w / 2}" fill="#fff" stroke="#b9bec7" stroke-width="2"/>')
        else:
            rx = 10
            if t in TRIGGERS:
                out.append(f'<path d="M{x + 40},{y} L{x + w - rx},{y} Q{x + w},{y} {x + w},{y + rx} L{x + w},{y + h - rx} Q{x + w},{y + h} {x + w - rx},{y + h} L{x + 40},{y + h} A40,50 0 0 1 {x + 40},{y} z" fill="#fff" stroke="#b9bec7" stroke-width="2"/>')
            else:
                out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="#fff" stroke="#b9bec7" stroke-width="2"/>')
            # handles
            labels = outputs_of(n)
            for i, lab in enumerate(labels):
                hy = y + h * (i + 1) / (len(labels) + 1)
                out.append(f'<circle cx="{x + w}" cy="{hy}" r="5" fill="#8a8f98"/>')
                if lab:
                    out.append(f'<text x="{x + w + 9}" y="{hy - 7}" font-size="12" fill="{"#e03131" if lab == "error" else "#5c636e"}">{esc(lab)}</text>')
            if t not in TRIGGERS:
                out.append(f'<circle cx="{x}" cy="{y + h / 2}" r="5" fill="#8a8f98"/>')
        fs = 30 if len(glyph) == 1 else 22
        out.append(f'<text x="{x + w / 2}" y="{y + h / 2 + fs * 0.36}" text-anchor="middle" font-size="{fs}" font-weight="700" fill="{col}">{esc(glyph)}</text>')
        if n.get('retryOnFail'):
            out.append(f'<text x="{x + w - 8}" y="{y + 16}" text-anchor="end" font-size="11" fill="#5f3dc4">↻{n.get("maxTries", 3)}</text>')
        for k, part in enumerate(wrap_name(n['name'], 18 if t != 'agent' else 30)):
            out.append(f'<text x="{x + w / 2}" y="{y + h + 20 + k * 16}" text-anchor="middle" font-size="13.5" font-weight="600" fill="#2b2b2b">{esc(part)}</text>')
    out.append('</svg>')
    return '\n'.join(out)

if __name__ == '__main__':
    wf = json.load(open(sys.argv[1], encoding='utf-8'))
    view = tuple(map(float, sys.argv[3:7])) if len(sys.argv) >= 7 else None
    open(sys.argv[2], 'w', encoding='utf-8').write(render(wf, view))
