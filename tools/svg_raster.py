"""
Rasterisation minimale d'un SVG de chemins (logo NINE HANDS | DSP) sans dependance externe (rsvg absent) :
analyse des commandes M L H V C S Q Z (absolues et relatives), courbes aplaties, remplissage par matplotlib (Agg).
render(svg_path, width_px) -> image RGBA (numpy uint8), fond transparent.
"""
import re
import numpy as np


def _tokens(d):
    for m in re.finditer(r'[MmLlHhVvCcSsQqZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?', d):
        yield m.group(0)


def _flatten(d, steps=10):
    toks = list(_tokens(d)); i = 0; cmd = None
    cur = np.zeros(2); start = np.zeros(2); last_c = None
    verts, codes = [], []
    def num():
        nonlocal i
        v = float(toks[i]); i += 1; return v
    while i < len(toks):
        if re.match(r'[A-Za-z]', toks[i]):
            cmd = toks[i]; i += 1
            if cmd in 'Zz':
                verts.append(tuple(start)); codes.append('Z'); cur = start.copy(); last_c = None
                continue
        rel = cmd.islower(); c = cmd.upper()
        base = cur if rel else np.zeros(2)
        if c == 'M':
            cur = base + [num(), num()]; start = cur.copy(); verts.append(tuple(cur)); codes.append('M')
            cmd = 'l' if rel else 'L'; last_c = None
        elif c == 'L':
            cur = base + [num(), num()]; verts.append(tuple(cur)); codes.append('L'); last_c = None
        elif c == 'H':
            x = num(); cur = np.array([x + (cur[0] if rel else 0), cur[1]]); verts.append(tuple(cur)); codes.append('L'); last_c = None
        elif c == 'V':
            y = num(); cur = np.array([cur[0], y + (cur[1] if rel else 0)]); verts.append(tuple(cur)); codes.append('L'); last_c = None
        elif c in 'CS':
            if c == 'C':
                p1 = base + [num(), num()]
            else:
                p1 = 2 * cur - last_c if last_c is not None else cur.copy()
            p2 = base + [num(), num()]; p3 = base + [num(), num()]
            for t in np.linspace(0, 1, steps + 1)[1:]:
                pt = (1 - t) ** 3 * cur + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
                verts.append(tuple(pt)); codes.append('L')
            last_c = p2; cur = p3
        elif c == 'Q':
            p1 = base + [num(), num()]; p2 = base + [num(), num()]
            for t in np.linspace(0, 1, steps + 1)[1:]:
                pt = (1 - t) ** 2 * cur + 2 * (1 - t) * t * p1 + t ** 2 * p2
                verts.append(tuple(pt)); codes.append('L')
            cur = p2; last_c = None
        else:
            i += 1
    return verts, codes


def render(svg_file, width_px):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    s = open(svg_file).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', s).group(1).split()]
    group_fill = re.findall(r'<g[^>]*fill="(#[0-9A-Fa-f]{6})"', s)
    gf = group_fill[0] if group_fill else '#000000'
    h_px = int(round(width_px * vb[3] / vb[2]))
    fig = plt.figure(figsize=(width_px / 100, h_px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(vb[0], vb[0] + vb[2]); ax.set_ylim(vb[1] + vb[3], vb[1]); ax.axis('off')
    fig.patch.set_alpha(0)
    for m in re.finditer(r'<path([^>]*)\sd="([^"]+)"', s, re.S):
        attrs, d = m.group(1), m.group(2)
        fm = re.search(r'fill="(#[0-9A-Fa-f]{6})"', attrs)
        col = fm.group(1) if fm else gf
        v, c = _flatten(d)
        mc = [Path.MOVETO if k == 'M' else (Path.CLOSEPOLY if k == 'Z' else Path.LINETO) for k in c]
        ax.add_patch(PathPatch(Path(v, mc), facecolor=col, edgecolor='none', antialiased=True))
    fig.canvas.draw()
    img = np.asarray(fig.canvas.buffer_rgba()).copy()
    plt.close(fig)
    return img
