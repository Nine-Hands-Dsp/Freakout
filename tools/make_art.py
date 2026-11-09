"""
FREAKOUT (NINE HANDS | DSP) - visuel du plugin, entierement recalcule (v1.3.0, nov. 2026).

Regle NINE HANDS | DSP des pedales simples : fond de 1235 x 1800 pixels, pedale plein cadre (le boitier touche le haut et le
bas de l'image, les jacks touchent les bords gauche et droit), fond transparent seulement autour des jacks et dans les coins
arrondis. Repere du plugin = image / 2 = 617,5 x 900 unites. Le dessin est calcule a 4 pixels par unite (2470 x 3600, « 4K »)
puis reduit a 2 pixels par unite : aretes, panneaux et pieces photo restent nets.

Design FreakOut (d'apres le visuel valide par l'utilisateur) : boitier en aluminium brosse, colonne FEEDBACK (9 LED rouges)
et colonne MOMENTARY / DRY en serigraphie noire, potard concentrique RANGE (GAIN au centre, ONSET en jupe), selecteur TYPE,
ecran (ligne d'etat + presets), titre FREAKOUT et onde de larsen, footswitch, logo NINE HANDS | DSP.
Pieces photo du kit NINE HANDS | DSP (photos de l'utilisateur) : potard, LED, footswitch, embases jack, inverseurs.
Une seule lumiere : en haut a gauche (ombres portees vers le bas a droite).

Le fond ne contient AUCUN texte : textes, graduations, filets, fleches, cadre grave, onde du titre et logo sont dessines
par le plugin en vectoriel (Layout.h), nets a toutes les tailles et sur les ecrans 4K / Retina.

Sorties (racine du depot) :
  background.png    fond 1235 x 1800 RGBA
  glow_strip.png    facade eclairee par l'echelle de LED, 5 etats cumulatifs (centre, puis paires vers l'exterieur)
  led_on.png        lentille allumee
  toggle_strip.png  inverseur : haut (ON) / milieu / bas (OFF)
  fs_down.png       footswitch enfonce (meme cadrage que le footswitch du fond)
  Layout.h, tools/layout.json, design/preview_art.png
Usage : python3 tools/make_art.py
"""
import os, sys, math, json
import numpy as np, cv2
from PIL import Image, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import photo_controls as PC
import toggle_photo as TP

AS = 4                                           # pixels par unite pendant le calcul (image finale : 2)
FW, FH = 617.5, 900.0                            # repere du plugin (image 1235 x 1800 / 2)
W, H = int(round(FW * AS)), int(round(FH * AS))
L = np.array([-0.46, -0.62, 0.64]); L /= np.linalg.norm(L)
HV = (L + np.array([0, 0, 1.0])); HV /= np.linalg.norm(HV)

# ------------------------------------------------------------------ geometrie (unites du plugin)
JACK_LEN = 112.0
_j = PC.jack_sprite(JACK_LEN, AS, 1)
JP = math.floor(_j[1] * AS) / AS                 # saillie d'une embase hors du boitier
BX0, BX1 = JP, FW - JP                           # boitier (le haut et le bas touchent l'image)
BY0, BY1 = 0.0, FH
BR = 36.0                                        # rayon des coins du boitier
EDGE = 11.0                                      # arete arrondie de l'aluminium moule
CX = FW / 2
FRAME = (BX0 + 17.0, 17.0, BX1 - BX0 - 34.0, FH - 34.0, 24.0)       # cadre grave (vectoriel)

PANEL_A = (58.0, 42.0, 118.0, 414.0)             # colonne FEEDBACK (x, y, w, h)
PANEL_B = (188.0, 42.0, 120.0, 414.0)            # colonne MOMENTARY / DRY
PANEL_R = 12.0
LED_X = 132.0
LEDS = [(LED_X, 82.0 + i * 42.0) for i in range(9)]
LED_LENS = 9.2
TOG = {'momentary': (248.0, 164.0), 'dry': (248.0, 360.0)}
TOG_WASHER, TOG_S = 23.5, 116.0
KX = 448.0                                       # colonne des potards
RANGE_C = (KX, 172.0); SKIRT_R, CAP_R = 64.0, 37.0
TYPE_C = (KX, 360.0); TYPE_R = 42.0
TYPE_ANG = [-135, -90, -45, 0, 45, 90, 135]      # SUB, 1ST, 2ND, 3RD, 5TH, NAT LOW, NAT HI
DISPLAY = (84.0, 478.0, 449.5, 86.0)             # verre de l'ecran (x, y, w, h)
ROW = (DISPLAY[0] + 12, DISPLAY[1] + 6, DISPLAY[2] - 24, 40.0)       # ligne d'etat
BAR = (DISPLAY[0] + 12, DISPLAY[1] + 50, DISPLAY[2] - 24, 28.0)      # barre de presets
JACK_Y = DISPLAY[1] + DISPLAY[3] / 2
TITLE_Y, SUB_Y = 618.0, 668.0
FS = (CX, 768.0); FS_FLATS = 106.0
LOGO_C, LOGO_W = (CX, 866.0), 170.0

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
UX, UY = (XX + 0.5) / AS, (YY + 0.5) / AS
rng = np.random.default_rng(7)

def rrect_sd(x, y, x0, y0, w, h, r):
    cx, cy = x0 + w / 2, y0 + h / 2
    qx = np.abs(x - cx) - (w / 2 - r); qy = np.abs(y - cy) - (h / 2 - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r

def over(dst, rgba, x0, y0):
    h, w = rgba.shape[:2]
    X0, Y0 = int(round(x0)), int(round(y0))
    sx0, sy0 = max(0, -X0), max(0, -Y0)
    ex, ey = min(w, dst.shape[1] - X0), min(h, dst.shape[0] - Y0)
    a = rgba[sy0:ey, sx0:ex, 3:4].astype(np.float32) / 255.0
    reg = dst[Y0 + sy0:Y0 + ey, X0 + sx0:X0 + ex]
    dst[Y0 + sy0:Y0 + ey, X0 + sx0:X0 + ex] = reg * (1 - a) + rgba[sy0:ey, sx0:ex, :3] * a

def noise(scale_x, scale_y, seed):
    """bruit lisse anisotrope (calcule petit puis agrandi : rapide et economique en memoire)"""
    r = np.random.default_rng(seed)
    sh = (max(2, int(H / scale_y) + 2), max(2, int(W / scale_x) + 2))
    n = r.standard_normal(sh).astype(np.float32)
    return cv2.resize(n, (W, H), interpolation=cv2.INTER_CUBIC)

print('boitier...')
# ------------------------------------------------------------------ 1. boitier : aluminium brosse, arete arrondie
sd = rrect_sd(UX, UY, BX0, BY0, BX1 - BX0, BY1 - BY0, BR)
body = np.clip(0.5 - sd * AS, 0, 1).astype(np.float32)
d_in = np.clip(-sd, 0, None)
hgt = np.where(d_in < EDGE, np.sqrt(np.clip(EDGE ** 2 - (EDGE - d_in) ** 2, 0, None)), EDGE).astype(np.float32)
del d_in
gy, gx = np.gradient(cv2.GaussianBlur(hgt, (0, 0), 1.2), 1.0 / AS)
nz = 1.0 / np.sqrt(gx * gx + gy * gy + 1.0)
nx, ny = -gx * nz, -gy * nz
del gx, gy
ndl = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
ndh = np.clip(nx * HV[0] + ny * HV[1] + nz * HV[2], 0, 1)
flat = np.clip((hgt - EDGE + 0.4) / 0.4, 0, 1)                 # 1 sur le dessus, 0 sur l'arete
del hgt, nx, ny, nz
# brossage horizontal : stries fines et longues + bandes plus larges, reflet anisotrope qui glisse en diagonale
streak = 0.62 * noise(260, 0.55, 1) + 0.38 * noise(70, 0.35, 2)
band = noise(140, 9, 3)
sheen = 0.55 + 0.45 * np.exp(-((UX - 210 - (UY - 300) * 0.22) / 210.0) ** 2)
grad = 1.0 - 0.09 * (UY / FH) + 0.04 * (1 - UX / FW)
lum = (168.0 + 36.0 * sheen) * grad + 7.0 * streak + 2.6 * band
del streak, band
lum += rng.standard_normal((H, W)).astype(np.float32) * 1.4
# arete : eclairage par la normale + reflet brillant, sablage leger
edge_l = 72.0 + 158.0 * ndl + 85.0 * ndh ** 30
lum = lum * flat + edge_l * (1 - flat)
del ndl, ndh, edge_l
tint = np.array([0.985, 0.995, 1.012], np.float32)
img = lum[..., None] * tint
del lum

print('serigraphie...')
# ------------------------------------------------------------------ 2. panneaux noirs (serigraphie satinee), pastilles RANGE / TYPE
INK = np.array([24.0, 24.0, 27.0], np.float32)
def ink_fill(mask, satin=1.0):
    global img
    m = mask[..., None]
    col = INK + (9.0 * sheen * grad)[..., None] * satin + rng.standard_normal((H, W)).astype(np.float32)[..., None] * 1.1
    img = img * (1 - m) + col * m
def rrect_mask(x, y, w, h, r):
    return np.clip(0.5 - rrect_sd(UX, UY, x, y, w, h, r) * AS, 0, 1).astype(np.float32)
pan = np.maximum(rrect_mask(*PANEL_A, PANEL_R), rrect_mask(*PANEL_B, PANEL_R))
ink_fill(pan)
PILLS = [(KX - 52, 50.0, 104.0, 26.0), (KX - 44, 434.0, 88.0, 26.0)]
for p in PILLS: ink_fill(rrect_mask(*p, 7.0))

# ------------------------------------------------------------------ 3. ecran : verre fume encastre (biseau clair en bas, ombre interne en haut)
dx0, dy0, dw, dh = DISPLAY
dsd = rrect_sd(UX, UY, dx0, dy0, dw, dh, 12.0)
dm = np.clip(0.5 - dsd * AS, 0, 1)[..., None]
din = np.clip(-dsd, 0, None)
glass = np.array([9.0, 10.0, 13.0], np.float32) + (7.0 * np.clip(1 - (UY - dy0) / 30.0, 0, 1))[..., None]
glass = glass * (1 - 0.6 * np.clip(1 - din / 5.0, 0, 1) * (UY < dy0 + dh / 2))[..., None]
refl = (np.exp(-((((UX - dx0) * 0.30 - (UY - dy0) * 1.0) - 6.0) / 9.0) ** 2) * 7.0)[..., None]
img = img * (1 - dm) + (glass + refl) * dm
bev = np.clip(1 - np.abs(dsd - 0.9) / 1.0, 0, 1) * (UY > dy0 + dh / 2) * 34.0
img += bev[..., None]
# fond sombre de la barre de presets (le cadre et le texte sont dessines par le plugin)
bm = rrect_mask(*BAR, 14.0)[..., None]
img = img * (1 - bm * 0.35)
del dsd, din, dm, glass, refl, bev, bm

print('pieces photo...')
# ------------------------------------------------------------------ 4. occlusion douce autour des pieces en relief
def occlusion(mask, strength=1.0):
    global img
    contact = cv2.GaussianBlur(mask, (0, 0), 2.5 * AS)
    soft = cv2.GaussianBlur(mask, (0, 0), 12.0 * AS)
    o = np.clip(contact * 0.5 + soft * 0.8, 0, 0.45) * strength * (1.0 - mask) * body
    img = img * (1.0 - o)[..., None]
occ = np.zeros((H, W), np.float32)
for (c, R) in ((RANGE_C, SKIRT_R), (TYPE_C, TYPE_R), (FS, FS_FLATS * 0.56)):
    occ = np.maximum(occ, np.clip((R - np.hypot(UX - c[0], UY - c[1])) * AS, 0, 1))
occlusion(occ)
del occ

# ------------------------------------------------------------------ 5. potards (photo du kit, repere efface : seuls les reperes du plugin tournent)
SK, SKS = PC.knob_sprite(SKIRT_R, AS)
over(img, SK, (RANGE_C[0] - SKS / 2) * AS, (RANGE_C[1] - SKS / 2) * AS)
CP, CPS = PC.knob_sprite(CAP_R, AS)                           # chapeau GAIN pose sur la jupe (son ombre tombe sur elle)
over(img, CP, (RANGE_C[0] - CPS / 2) * AS, (RANGE_C[1] - CPS / 2) * AS)
TK, TKS = PC.knob_sprite(TYPE_R, AS)
over(img, TK, (TYPE_C[0] - TKS / 2) * AS, (TYPE_C[1] - TKS / 2) * AS)

# ------------------------------------------------------------------ 6. LED : lentilles eteintes (photo de l'utilisateur)
LD, LDON, LS = PC.led_sprites(LED_LENS, AS, colour='red')
for (lx, ly) in LEDS:
    over(img, LD, (lx - LS / 2) * AS, (ly - LS / 2) * AS)
LED_RING = LED_LENS * 1.07

# ------------------------------------------------------------------ 7. footswitch (photo du kit, reference Echoflex) + version enfoncee
FSPR, _refl, FS_W, FS_BTN = PC.footswitch_sprite(FS_FLATS, AS)
fs_x0, fs_y0 = (FS[0] - FS_W / 2) * AS, (FS[1] - FS_W / 2) * AS
over(img, FSPR, fs_x0, fs_y0)

def pressed_footswitch():
    """bouton enfonce : il descend dans l'ecrou (un peu plus petit, moins de lumiere sur le dessus), le rebord de l'ecrou
    porte une ombre en croissant sur son bord haut gauche ; l'ecrou ne bouge pas"""
    n = FSPR.shape[0]
    spr = FSPR.astype(np.float32).copy()
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = n / 2.0
    rb = FS_BTN * AS                                       # rayon du bouton (px)
    r = np.hypot(xx - c, yy - c)
    btn = np.clip((rb * 1.02 - r) / 1.5, 0, 1)
    k = 0.94
    M = np.float32([[k, 0, (1 - k) * c + 0.4 * AS], [0, k, (1 - k) * c + 0.7 * AS]])
    small = cv2.warpAffine(spr, M, (n, n), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    sb = np.clip((rb * k * 1.0 - np.hypot(xx - c - 0.4 * AS, yy - c - 0.7 * AS)) / 1.5, 0, 1)
    # fond du logement (sombre) visible autour du bouton enfonce
    well = spr.copy(); well[..., :3] *= 0.42
    out = spr * (1 - btn[..., None]) + well * btn[..., None]
    top = small.copy(); top[..., :3] *= 0.90
    out = out * (1 - sb[..., None]) + top * sb[..., None]
    # ombre du rebord : croissant en haut a gauche du bouton
    dx, dy = (xx - c) / rb, (yy - c) / rb
    cres = np.clip(1.0 - np.hypot(dx + 0.10, dy + 0.14) / 0.98, 0, 1)
    cres = np.clip((0.22 - cres) / 0.22, 0, 1) * sb * np.clip(-(dx + dy) * 0.9 + 0.3, 0, 1)
    out[..., :3] *= (1 - 0.55 * cres)[..., None]
    # alpha : seulement l'ecrou et le bouton (pas l'ombre portee, deja dans le fond) -> la couronne vectorielle reste visible
    obj = np.clip((spr[..., 3] / 255.0 - 0.90) / 0.10, 0, 1)
    return np.dstack([out[..., :3], obj * 255.0])
FS_DOWN = pressed_footswitch()

# ------------------------------------------------------------------ 8. embases jack (photo du kit) : OUT a gauche, IN a droite
alpha = body.copy()
for side in (-1, 1):
    j, jw_u, jh_u = PC.jack_sprite(JACK_LEN, AS, side)
    jh, jw = j.shape[:2]
    jw2 = int(round(JP * AS))
    if jw2 != jw:
        pm_ = j.copy(); pm_[..., :3] *= pm_[..., 3:4] / 255.0
        pm_ = cv2.resize(pm_, (jw2, jh), interpolation=cv2.INTER_AREA)
        a_ = np.maximum(pm_[..., 3:4], 1e-3); pm_[..., :3] = np.where(pm_[..., 3:4] > 0.5, pm_[..., :3] * 255.0 / a_, 0)
        j = pm_; jw = jw2
    x0 = 0 if side < 0 else W - jw
    y0 = int(round(JACK_Y * AS - jh / 2))
    o = np.zeros((H, W), np.float32)
    o[y0:y0 + jh, x0:x0 + jw] = j[..., 3] / 255.0
    contact = cv2.GaussianBlur(o, (0, 0), 3.0 * AS)
    soft = cv2.GaussianBlur(o, (0, 0), 16.0 * AS)
    oc = np.clip(contact * 0.9 + soft * 1.5, 0, 0.55) * (0.7 if side < 0 else 0.25)   # lumiere a gauche : ombre plus marquee a gauche
    img *= (1.0 - oc * body)[..., None]
    over(img, j, x0, y0)
    alpha = np.maximum(alpha, o)
    del o, contact, soft, oc

# ------------------------------------------------------------------ 9. sorties a 2 px par unite
def half(a):
    return cv2.resize(a, (int(round(FW * 2)), int(round(FH * 2))), interpolation=cv2.INTER_AREA)
out_rgb = np.clip(half(img), 0, 255); out_a = np.clip(half(alpha), 0, 1)
Image.fromarray(np.dstack([out_rgb, out_a * 255]).astype(np.uint8), 'RGBA').save(os.path.join(ROOT, 'background.png'), optimize=True)
for old in ('background.jpg', 'fs_refl.png'):
    if os.path.exists(os.path.join(ROOT, old)): os.remove(os.path.join(ROOT, old))
def half_sprite(s, n2):
    pm = s.astype(np.float32).copy(); pm[..., :3] *= pm[..., 3:4] / 255.0
    sm = cv2.resize(pm, (n2, n2), interpolation=cv2.INTER_AREA)
    a = np.clip(sm[..., 3:4], 0, 255); rgb = np.where(a > 0.5, sm[..., :3] * 255.0 / np.maximum(a, 1e-3), 0)
    return np.dstack([rgb, a]).astype(np.uint8)
Image.fromarray(half_sprite(LDON, int(round(LS * 2))), 'RGBA').save(os.path.join(ROOT, 'led_on.png'))
Image.fromarray(half_sprite(FS_DOWN, int(round(FS_W * 2))), 'RGBA').save(os.path.join(ROOT, 'fs_down.png'))
tframes = TP.frames(TOG_WASHER, TOG_S, 2)                      # inverseurs : photos du kit, 2 px par unite
Image.fromarray(np.concatenate(tframes, 0), 'RGBA').save(os.path.join(ROOT, 'toggle_strip.png'))

print('lumiere des LED...')
# ------------------------------------------------------------------ 10. facade eclairee par l'echelle de LED (5 etats cumulatifs, calque alpha)
GL = (LED_X - 56.0, LEDS[0][1] - 56.0, 112.0, LEDS[-1][1] - LEDS[0][1] + 112.0)
gx0, gy0 = int(round(GL[0] * AS)), int(round(GL[1] * AS))
gw, gh = int(round(GL[2] * AS)), int(round(GL[3] * AS))
reg = img[gy0:gy0 + gh, gx0:gx0 + gw].astype(np.float32)
gyy, gxx = np.mgrid[0:gh, 0:gw].astype(np.float32)
gux, guy = (gxx + gx0 + 0.5) / AS, (gyy + gy0 + 0.5) / AS
lumr = reg.mean(2, keepdims=True)
col = np.array([1.0, 0.20, 0.10], np.float32)
order = [[4], [3, 5], [2, 6], [1, 7], [0, 8]]
lit_i, layers = [], []
for st in order:
    lit_i += st
    E = np.zeros((gh, gw), np.float32)
    for i in lit_i:
        lx, ly = LEDS[i]
        d = np.hypot(gux - lx, guy - ly)
        h1, h2 = 6.0, 22.0
        e = 1.0 * h1 ** 3 / (d ** 2 + h1 ** 2) ** 1.5 + 0.16 * h2 ** 3 / (d ** 2 + h2 ** 2) ** 1.5
        e[d < LED_RING] = 0.0
        E += e
    lit = reg + (reg * 2.4 + 14.0 * np.clip(lumr / 40.0, 0.3, 1.6)) * E[..., None] * col
    add = lit - reg
    a = np.clip(np.abs(add).max(-1) / 12.0, 0, 1)
    rgb = np.where(a[..., None] > 1e-3, reg + add / np.maximum(a, 1e-3)[..., None], reg)
    rgba = np.dstack([np.clip(rgb, 0, 255) * a[..., None], a * 255])     # alpha premultiplie pour la reduction
    sm = cv2.resize(rgba, (int(round(GL[2] * 2)), int(round(GL[3] * 2))), interpolation=cv2.INTER_AREA)
    aa = np.maximum(sm[..., 3:4] / 255.0, 1e-4)
    layers.append(np.dstack([np.clip(sm[..., :3] / aa, 0, 255), sm[..., 3:4]]).astype(np.uint8))
Image.fromarray(np.concatenate(layers, 0), 'RGBA').save(os.path.join(ROOT, 'glow_strip.png'), optimize=True)

# ------------------------------------------------------------------ 11. serigraphie vectorielle (dessinee par le plugin) : textes, graduations, filets, fleches
FONTS = os.path.join(ROOT, 'assets', 'fonts')
FONT_FILES = {'medium': 'Poppins-Medium.ttf', 'bold': 'Poppins-Bold.ttf', 'light': 'Poppins-Light.ttf', 'regular': 'Poppins-Regular.ttf'}
FK = {'medium': 0, 'bold': 1, 'light': 2, 'regular': 3}
DARK, LIGHT = 0, 1                                # encre noire sur le metal / encre claire sur les panneaux noirs
TXT, LINES, TRIS = [], [], []
def text(s, x, y, em, font='medium', track=0.0, ink=DARK, rot=0.0):
    TXT.append((s, FK[font], em, track, x, y, rot, ink))
def width(s, em, font='medium', track=0.0):
    f = ImageFont.truetype(os.path.join(FONTS, FONT_FILES[font]), 200)
    return sum(f.getlength(c) for c in s) * em / 200.0 * 1.0 + track * (len(s) - 1)
def line(x0, y0, x1, y1, w, ink=DARK):
    LINES.append((x0, y0, x1, y1, w, ink))
def tri(x0, y0, x1, y1, x2, y2, ink=DARK):
    TRIS.append((x0, y0, x1, y1, x2, y2, ink))

# colonne FEEDBACK
ax_, ay0, ay1 = PANEL_A[0] + 100.0, PANEL_A[1] + 18.0, PANEL_A[1] + PANEL_A[3] - 18.0
text('FEEDBACK', PANEL_A[0] + 24.0, (ay0 + ay1) / 2, 15.0, 'bold', 4.6, LIGHT, 90.0)
for i, (lx, ly) in enumerate(LEDS):
    ln = 15.0 - abs(i - 4) * 2.2                                    # graduations plus longues au centre (lecture du centre vers l'exterieur)
    line(lx + 15.0, ly, lx + 15.0 + ln, ly, 1.6, LIGHT)
line(ax_ + 4.0, ay0 + 8.0, ax_ + 4.0, ay1 - 8.0, 1.2, LIGHT)
tri(ax_ + 4.0, ay0, ax_ - 0.5, ay0 + 9.0, ax_ + 8.5, ay0 + 9.0, LIGHT)
tri(ax_ + 4.0, ay1, ax_ - 0.5, ay1 - 9.0, ax_ + 8.5, ay1 - 9.0, LIGHT)

# colonne MOMENTARY / DRY
bx = PANEL_B[0] + PANEL_B[2] / 2
for title_, (tx, ty), em in (('MOMENTARY', TOG['momentary'], 14.0), ('DRY', TOG['dry'], 16.0)):
    text(title_, bx, ty - 96.0, em, 'bold', 1.6, LIGHT)
    line(bx - 44.0, ty - 82.0, bx + 44.0, ty - 82.0, 1.3, LIGHT)
    text('ON', bx, ty - 58.0, 13.0, 'medium', 2.0, LIGHT)
    text('OFF', bx, ty + 60.0, 13.0, 'medium', 2.0, LIGHT)
line(PANEL_B[0], TOG['dry'][1] - 116.0, PANEL_B[0] + PANEL_B[2], TOG['dry'][1] - 116.0, 2.4, LIGHT)

# RANGE : pastille, graduations, MIN / MAX, GAIN (centre) / ONSET (jupe) avec pictogramme concentrique
text('RANGE', PILLS[0][0] + PILLS[0][2] / 2, PILLS[0][1] + PILLS[0][3] / 2 + 0.5, 14.5, 'bold', 3.0, LIGHT)
rx, ry = RANGE_C
for i in range(31):
    a = math.radians(-150 + 10 * i)
    big = i % 5 == 0
    r0, r1 = SKIRT_R + 7.0, SKIRT_R + (15.0 if big else 11.0)
    line(rx + r0 * math.sin(a), ry - r0 * math.cos(a), rx + r1 * math.sin(a), ry - r1 * math.cos(a), 1.7 if big else 1.2)
text('MIN', rx - 66.0, ry + 68.0, 10.0, 'medium', 1.0)
text('MAX', rx + 66.0, ry + 68.0, 10.0, 'medium', 1.0)
text('GAIN', rx - 38.0, ry + 92.0, 13.0, 'bold', 1.6)
text('ONSET', rx + 40.0, ry + 92.0, 13.0, 'bold', 1.6)
ICONS = [((rx - 38.0 - width('GAIN', 13.0, 'bold', 1.6) / 2 - 11.0, ry + 92.0), True),
         ((rx + 40.0 + width('ONSET', 13.0, 'bold', 1.6) / 2 + 11.0, ry + 92.0), False)]

# TYPE : 7 positions, pastille
tx_, ty_ = TYPE_C
TYPE_LAB = ['SUB', '1ST', '2ND', '3RD', '5TH', 'NAT\nLOW', 'NAT\nHI']
for a_, lab in zip(TYPE_ANG, TYPE_LAB):
    a = math.radians(a_)
    rr = TYPE_R + (30.0 if '\n' not in lab else 33.0)
    lx, ly = tx_ + rr * math.sin(a), ty_ - rr * math.cos(a)
    if '\n' in lab:
        l1, l2 = lab.split('\n')
        text(l1, lx, ly - 7.0, 12.0, 'bold', 0.8); text(l2, lx, ly + 7.0, 12.0, 'bold', 0.8)
    else:
        text(lab, lx, ly, 12.5, 'bold', 0.8)
    r0, r1 = TYPE_R + 5.0, TYPE_R + 12.0
    line(tx_ + r0 * math.sin(a), ty_ - r0 * math.cos(a), tx_ + r1 * math.sin(a), ty_ - r1 * math.cos(a), 2.0)
text('TYPE', PILLS[1][0] + PILLS[1][2] / 2, PILLS[1][1] + PILLS[1][3] / 2 + 0.5, 14.5, 'bold', 3.0, LIGHT)

# OUT / IN a la hauteur des jacks, fleche vers la tranche
for lab, x0, d in (('OUT', BX0 + 38.0, -1), ('IN', BX1 - 38.0, 1)):
    text(lab, x0, JACK_Y - 7.0, 12.5, 'bold', 1.0)
    yA = JACK_Y + 9.0
    tri(x0 + 5.0 * d, yA, x0 - 3.0 * d, yA - 4.5, x0 - 3.0 * d, yA + 4.5)

# titre, sous-titre, onde de larsen qui gonfle (petite a gauche, ample a droite), avec reserve autour du titre
TITLE_EM, TITLE_TRACK = 62.0, 3.0
text('FREAKOUT', CX, TITLE_Y, TITLE_EM, 'bold', TITLE_TRACK)
tw = width('FREAKOUT', TITLE_EM, 'bold', TITLE_TRACK)
text('HARMONIC  FEEDBACK  GENERATOR', CX, SUB_Y, 13.0, 'medium', 3.4)
WAVE = []
xa, xb = FRAME[0] + 14.0, FRAME[0] + FRAME[2] - 14.0
g0, g1 = CX - tw / 2 - 10.0, CX + tw / 2 + 10.0
seg = []
for k in range(1601):
    u = k / 1600.0
    x = xa + (xb - xa) * u
    amp = 0.8 + 24.0 * (math.exp(4.4 * u) - 1) / (math.exp(4.4) - 1)
    y = TITLE_Y + 2.0 + amp * math.sin(2 * math.pi * (3.5 * u + 15.0 * u * u))
    if g0 < x < g1:
        if len(seg) > 1: WAVE.append(seg)
        seg = []
    else:
        seg.append((x, y))
if len(seg) > 1: WAVE.append(seg)

# couronne graduee autour du footswitch
FS_RING = 74.0
for i in range(36):
    a = math.radians(i * 10.0)
    big = i % 3 == 0
    r0, r1 = FS_RING + 3.0, FS_RING + (9.0 if big else 6.0)
    line(FS[0] + r0 * math.cos(a), FS[1] + r0 * math.sin(a), FS[0] + r1 * math.cos(a), FS[1] + r1 * math.sin(a), 1.4 if big else 1.0)

# ------------------------------------------------------------------ 12. Layout.h et layout.json
def f(v): return f"{v:.2f}f"
def PT(p): return "{ %s, %s }" % (f(p[0]), f(p[1]))
def RC(r): return "{ %s, %s, %s, %s }" % (f(r[0]), f(r[1]), f(r[2]), f(r[3]))
json.dump({"frame": [FW, FH], "leds": LEDS, "range": RANGE_C, "skirtR": SKIRT_R, "capR": CAP_R, "type": TYPE_C, "typeR": TYPE_R,
           "toggles": TOG, "togS": TOG_S, "fs": FS, "fsS": FS_W, "footR": FS_BTN, "display": DISPLAY, "row": ROW, "bar": BAR,
           "jackY": JACK_Y, "jackL": JP / 2, "jackR": FW - JP / 2, "body": [BX0, BY0, BX1 - BX0, BY1 - BY0], "title": TITLE_Y},
          open(os.path.join(HERE, 'layout.json'), 'w'), indent=1)
with open(os.path.join(ROOT, 'Layout.h'), 'w') as fo:
    fo.write(f"// genere par tools/make_art.py - ne pas modifier a la main (repere {FW} x {FH} = fond 1235 x 1800 px / 2)\n#pragma once\n#include <juce_graphics/juce_graphics.h>\nnamespace layout\n{{\n")
    fo.write(f"    constexpr float frameW = {f(FW)}, frameH = {f(FH)};   // pedale plein cadre (jacks aux bords gauche / droit)\n")
    fo.write("    const juce::Point<float> ledPos[9] = { " + ", ".join(PT(p) for p in LEDS) + " };\n")
    fo.write(f"    const float ledS = {f(LS)};   // sprite de la lentille allumee\n")
    fo.write(f"    const juce::Rectangle<float> glowRect {RC(GL)};\n")
    fo.write(f"    const juce::Point<float> rangePos {PT(RANGE_C)}, typePos {PT(TYPE_C)};\n")
    fo.write(f"    const float skirtR = {f(SKIRT_R)}, capR = {f(CAP_R)}, typeR = {f(TYPE_R)};\n")
    fo.write("    // repere creme des potards (photo) : de 0,28 a 0,90 du rayon sur le dessus\n")
    fo.write(f"    const juce::Point<float> momentaryPos {PT(TOG['momentary'])}, dryPos {PT(TOG['dry'])}; const float togS = {f(TOG_S)};\n")
    fo.write(f"    const juce::Point<float> fsPos {PT(FS)}; const float footR = {f(FS_BTN)}, fsS = {f(FS_W)};\n")
    fo.write(f"    const juce::Rectangle<float> displayRect {RC(DISPLAY)}, statusRect {RC(ROW)}, presetRect {RC(BAR)};\n")
    fo.write(f"    const float jackY = {f(JACK_Y)};\n")
    fo.write(f"    // cadre grave (x, y, w, h, rayon), dessine en vectoriel\n    const float frame[5] = {{ {', '.join(f(v) for v in FRAME)} }};\n")
    fo.write("    // serigraphie vectorielle : texte, police (0 medium, 1 bold, 2 light, 3 regular), taille, espacement, centre, rotation, encre (0 noire, 1 claire)\n")
    fo.write("    struct Txt { const char* s; int font; float em, track, x, y, rot; int ink; };\n")
    fo.write("    const Txt texts[] = {\n" + ",\n".join(f'        {{ "{t[0]}", {t[1]}, {f(t[2])}, {f(t[3])}, {f(t[4])}, {f(t[5])}, {f(t[6])}, {t[7]} }}' for t in TXT) + "\n    };\n")
    fo.write("    struct Seg { float x0, y0, x1, y1, w; int ink; };\n")
    fo.write("    const Seg lines[] = {\n" + ",\n".join(f"        {{ {f(l[0])}, {f(l[1])}, {f(l[2])}, {f(l[3])}, {f(l[4])}, {l[5]} }}" for l in LINES) + "\n    };\n")
    fo.write("    struct Tri { float x0, y0, x1, y1, x2, y2; int ink; };\n")
    fo.write("    const Tri tris[] = { " + ", ".join(f"{{ {', '.join(f(v) for v in t[:6])}, {t[6]} }}" for t in TRIS) + " };\n")
    fo.write("    // pictogrammes concentriques (centre, plein = GAIN / anneau = ONSET)\n")
    fo.write("    struct Ico { float x, y; bool inner; };\n")
    fo.write("    const Ico icons[] = { " + ", ".join(f"{{ {f(i[0][0])}, {f(i[0][1])}, {'true' if i[1] else 'false'} }}" for i in ICONS) + " };\n")
    fo.write(f"    // onde du titre : {len(WAVE)} troncons (points x, y)\n")
    for k, sgm in enumerate(WAVE):
        pts = sgm[::4] + [sgm[-1]]
        fo.write(f"    const float wave{k}[] = {{ " + ", ".join(f"{f(p[0])}, {f(p[1])}" for p in pts) + " };\n")
    fo.write("    struct WaveSeg { const float* p; int n; };\n")
    fo.write("    const WaveSeg wave[] = { " + ", ".join(f"{{ wave{k}, {len(s[::4]) + 1} }}" for k, s in enumerate(WAVE)) + " };\n")
    fo.write(f"    const float waveW = 2.2f, fsRing = {f(FS_RING)};\n")
    fo.write(f"    const juce::Point<float> logoPos {PT(LOGO_C)}; const float logoW = {f(LOGO_W)};\n")
    fo.write("}\n")

# ------------------------------------------------------------------ 13. apercu (LED du centre et 2 paires allumees, serigraphie esquissee)
print('apercu...')
from PIL import ImageDraw
import svg_raster
pv = Image.fromarray(np.dstack([out_rgb, out_a * 255]).astype(np.uint8), 'RGBA')
glow = Image.fromarray(layers[2]); pv.alpha_composite(glow, (int(round(GL[0] * 2)), int(round(GL[1] * 2))))
lon = Image.open(os.path.join(ROOT, 'led_on.png'))
for i in (2, 3, 4, 5, 6):
    lx, ly = LEDS[i]; pv.alpha_composite(lon, (int(round((lx - LS / 2) * 2)), int(round((ly - LS / 2) * 2))))
SS = 2
K = 2 * SS
lay = {DARK: Image.new('L', (int(FW * K), int(FH * K)), 0), LIGHT: Image.new('L', (int(FW * K), int(FH * K)), 0)}
for (s, fk, em, track, x, y, rot, ink) in TXT:
    font = ImageFont.truetype(os.path.join(FONTS, list(FONT_FILES.values())[fk]), max(1, int(em * K)))
    ws = [font.getlength(c) for c in s]; tot = sum(ws) + track * K * (len(s) - 1)
    t = Image.new('L', (int(tot) + 8, int(em * K * 1.8)), 0); td = ImageDraw.Draw(t); xx = 4
    for c, w_ in zip(s, ws): td.text((xx, t.height / 2), c, font=font, fill=255, anchor='lm'); xx += w_ + track * K
    if rot: t = t.rotate(rot, expand=True, resample=Image.BICUBIC)
    lay[ink].paste(255, (int(x * K - t.width / 2), int(y * K - t.height / 2)), t)
for ink in (DARK, LIGHT):
    d = ImageDraw.Draw(lay[ink])
    for l in LINES:
        if l[5] == ink: d.line([l[0] * K, l[1] * K, l[2] * K, l[3] * K], fill=255, width=max(1, int(l[4] * K)))
    for t in TRIS:
        if t[6] == ink: d.polygon([(t[0] * K, t[1] * K), (t[2] * K, t[3] * K), (t[4] * K, t[5] * K)], fill=255)
dd = ImageDraw.Draw(lay[DARK])
for sgm in WAVE: dd.line([(p[0] * K, p[1] * K) for p in sgm], fill=255, width=int(2.2 * K), joint='curve')
x0f, y0f, wf, hf, rf = FRAME
dd.rounded_rectangle([x0f * K, y0f * K, (x0f + wf) * K, (y0f + hf) * K], radius=int(rf * K), outline=255, width=int(1.6 * K))
dd.ellipse([(FS[0] - FS_RING) * K, (FS[1] - FS_RING) * K, (FS[0] + FS_RING) * K, (FS[1] + FS_RING) * K], outline=255, width=int(1.8 * K))
for (p, inner) in ICONS:
    dd.ellipse([(p[0] - 5.5) * K, (p[1] - 5.5) * K, (p[0] + 5.5) * K, (p[1] + 5.5) * K], outline=255, width=int(1.4 * K))
    if inner: dd.ellipse([(p[0] - 2.4) * K, (p[1] - 2.4) * K, (p[0] + 2.4) * K, (p[1] + 2.4) * K], fill=255)
pa = np.asarray(pv).astype(np.float32)
for ink, colr in ((DARK, (26, 26, 29)), (LIGHT, (220, 220, 216))):
    m = cv2.resize(np.asarray(lay[ink], np.float32) / 255.0, (pa.shape[1], pa.shape[0]), interpolation=cv2.INTER_AREA)[..., None]
    pa[..., :3] = pa[..., :3] * (1 - m) + np.array(colr, np.float32) * m
logo = svg_raster.render(os.path.join(ROOT, 'NineHandsLogo.svg'), int(LOGO_W * 2)).astype(np.float32)
lh = logo.shape[0]; lx0, ly0 = int(LOGO_C[0] * 2 - logo.shape[1] / 2), int(LOGO_C[1] * 2 - lh / 2)
la = logo[..., 3:4] / 255.0 * 0.92
pa[ly0:ly0 + lh, lx0:lx0 + logo.shape[1], :3] = pa[ly0:ly0 + lh, lx0:lx0 + logo.shape[1], :3] * (1 - la) + logo[..., :3] * la
# pointeurs creme (12 h) sur les potards
pv2 = Image.fromarray(pa.astype(np.uint8), 'RGBA'); d2 = ImageDraw.Draw(pv2)
for (c, R) in ((RANGE_C, CAP_R), (TYPE_C, TYPE_R)):
    d2.line([c[0] * 2, (c[1] - 0.28 * R) * 2, c[0] * 2, (c[1] - 0.90 * R) * 2], fill=(232, 225, 214, 255), width=int(0.075 * R * 2))
a_ = math.radians(-60)
d2.line([(RANGE_C[0] + 0.70 * SKIRT_R * math.sin(a_)) * 2, (RANGE_C[1] - 0.70 * SKIRT_R * math.cos(a_)) * 2,
         (RANGE_C[0] + 0.93 * SKIRT_R * math.sin(a_)) * 2, (RANGE_C[1] - 0.93 * SKIRT_R * math.cos(a_)) * 2], fill=(232, 225, 214, 255), width=6)
for key, fr in (('momentary', 2), ('dry', 0)):
    t_ = Image.fromarray(tframes[fr]); c_ = TOG[key]
    pv2.alpha_composite(t_, (int(round((c_[0] - TOG_S / 2) * 2)), int(round((c_[1] - TOG_S / 2) * 2))))
os.makedirs(os.path.join(ROOT, 'design'), exist_ok=True)
bgc = Image.new('RGBA', pv2.size, (17, 17, 18, 255)); bgc.alpha_composite(pv2)
bgc.convert('RGB').save(os.path.join(ROOT, 'design', 'preview_art.png'))
print('ok', 'JP', JP, 'boitier', BX1 - BX0, 'x', FH)
