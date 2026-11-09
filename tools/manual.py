# FREAKOUT (NINE HANDS | DSP) - notice PDF en francais, illustree avec le rendu reel du plugin (v1.3 : fond 1235 x 1800, repere 617,5 x 900).
# Usage : python3 tools/manual.py <dossier des captures (tools/render)> <fichier PDF de sortie>
#   ou   : python3 tools/manual.py tools/manual_assets <fichier PDF> (images deja composees, reprises de la notice v1.1.0 :
#          freakout_annotated / knobs / ctl / leds / disp / cover_cutout.png)
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (BaseDocTemplate, PageTemplate, NextPageTemplate, Frame, Paragraph, Spacer, Image as RLImage,
                                Table, TableStyle, PageBreak, CondPageBreak, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = sys.argv[1]
OUT = sys.argv[2]
VERSION = "1.3.1"
TMP = os.path.dirname(os.path.abspath(OUT))
FONTS = os.path.join(ROOT, "assets", "fonts")

for n, f in (("Pop", "Poppins-Regular"), ("PopL", "Poppins-Light"), ("PopM", "Poppins-Medium"), ("PopB", "Poppins-Bold"),
             ("Title", "BarlowCondensed-ExtraBold")):
    pdfmetrics.registerFont(TTFont(n, os.path.join(FONTS, f + ".ttf")))

ACC = colors.HexColor("#D6301C"); ACC_L = colors.HexColor("#FF6A4D")       # rouge des LED du visuel
DARK = colors.HexColor("#1B1C20"); GREY = colors.HexColor("#686A72"); LIGHT = colors.HexColor("#EEEEEC")

LAY = json.load(open(os.path.join(ROOT, "tools", "layout.json")))

PREBUILT = not os.path.exists(os.path.join(SHOTS, "freakout_status.png"))
if PREBUILT:   # images deja composees (tools/manual_assets, reprises de la notice precedente)
    annotated, knobs_img, ctl_img, leds_img, disp_img, cover = (os.path.join(SHOTS, "freakout_" + n + ".png")
        for n in ("annotated", "knobs", "ctl", "leds", "disp", "cover_cutout"))
else:
    def shot(name): return Image.open(os.path.join(SHOTS, name)).convert("RGB")
    src = shot("freakout_status.png")
    K = src.height / 900.0                                   # repere du plugin v1.3 : 617,5 x 900 unites (fond 1235 x 1800 / 2)

    # ---------- capture annotee ----------
    ann = src.copy(); dr = ImageDraw.Draw(ann)
    fnt = ImageFont.truetype(os.path.join(FONTS, "Poppins-Bold.ttf"), 30)
    led_mid = LAY["leds"][4]; rg = LAY["range"]; ty = LAY["type"]; tg = LAY["toggles"]; dsp = LAY["display"]
    marks = [  # numero, x, y (unites du plugin)
        (1, led_mid[0] - 50, led_mid[1]), (2, tg["momentary"][0] + 46, tg["momentary"][1] - 10), (3, tg["dry"][0] + 46, tg["dry"][1] - 10),
        (4, rg[0] + 20, rg[1] + 4), (5, rg[0] + 70, rg[1] - 58), (6, ty[0] - 70, ty[1] - 46),
        (7, dsp[0] + 18, dsp[1] + 26), (8, dsp[0] + 18, dsp[1] + 64), (9, LAY["fs"][0] + 84, LAY["fs"][1] - 52),
        (10, 54, LAY["jackY"] - 44), (11, 563, LAY["jackY"] - 44)]
    for n, x, y in marks:
        cx, cy, r = x * K, y * K, 24
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255), outline=(214, 48, 28), width=5)
        dr.text((cx, cy + 1), str(n), font=fnt, fill=(27, 28, 32), anchor="mm")
    annotated = os.path.join(TMP, "freakout_annotated.png"); ann.save(annotated)

    def crop_u(img_, box):
        k = img_.height / 900.0                       # chaque capture a sa propre taille
        return img_.crop(tuple(int(v * k) for v in box)).resize((int((box[2] - box[0]) * 2), int((box[3] - box[1]) * 2)), Image.LANCZOS)
    def strip(images, path, gap=16):
        h = max(i.height for i in images)
        s_ = Image.new("RGB", (sum(i.width for i in images) + gap * (len(images) - 1), h), (255, 255, 255))
        x = 0
        for i in images: s_.paste(i, (x, 0)); x += i.width + gap
        s_.save(path); return path

    # echelle de LED : effet actif (LED centrale), bypass, montee du larsen, pleine intensite
    lb = (led_mid[0] - 34, 48, led_mid[0] + 44, 450)
    leds_img = strip([crop_u(shot(p), lb) for p in ("freakout_default.png", "freakout_bypass.png", "freakout_bloom.png", "freakout_full.png")],
                     os.path.join(TMP, "freakout_leds.png"))
    # inverseurs (OFF / ON) et footswitch (relache / enfonce)
    tb = (tg["momentary"][0] - 60, 50, tg["momentary"][0] + 60, 456)
    fb = (LAY["fs"][0] - 86, LAY["fs"][1] - 86, LAY["fs"][0] + 86, LAY["fs"][1] + 86)
    ctl_img = strip([crop_u(shot("freakout_status.png"), tb), crop_u(shot("freakout_pressed.png"), tb),
                     crop_u(shot("freakout_full.png"), fb), crop_u(shot("freakout_pressed.png"), fb)], os.path.join(TMP, "freakout_ctl.png"))
    # ecran
    disp_img = os.path.join(TMP, "freakout_disp.png")
    dbox = (dsp[0] - 6, dsp[1] - 6, dsp[0] + dsp[2] + 6, dsp[1] + dsp[3] + 6)
    strip([crop_u(shot("freakout_bloom.png"), dbox), crop_u(shot("freakout_status.png"), dbox)], disp_img, gap=10)
    # potards
    knobs_img = strip([crop_u(shot("freakout_full.png"), (rg[0] - 100, rg[1] - 130, rg[0] + 100, rg[1] + 104)),
                       crop_u(shot("freakout_full.png"), (ty[0] - 100, ty[1] - 92, ty[0] + 100, ty[1] + 102))],
                      os.path.join(TMP, "freakout_knobs.png"))

    # ---------- couverture : pedale detouree avec le canal alpha du fond (boitier + jacks), reflet au sol, halo rouge tres doux ----------
    cov = shot("freakout_full.png")
    msk = Image.open(os.path.join(ROOT, "background.png")).split()[3].resize(cov.size, Image.LANCZOS)
    cut = Image.new("RGBA", cov.size, (0, 0, 0, 0)); cut.paste(cov, (0, 0), msk)
    cut = cut.crop(cut.getbbox())
    cw, ch = cut.size
    pad = int(cw * 0.16)
    canvas = Image.new("RGBA", (cw + 2 * pad, int(ch * 1.30) + pad), (0, 0, 0, 255))
    yy, xx = np.mgrid[0:canvas.height, 0:canvas.width].astype(np.float64)
    gcx, gcy = canvas.width / 2, pad + ch * 0.45
    glow = np.exp(-(((xx - gcx) / (cw * 0.62)) ** 2 + ((yy - gcy) / (ch * 0.48)) ** 2)) * 30
    edge = np.clip(np.minimum.reduce([xx, canvas.width - 1 - xx, yy, canvas.height - 1 - yy]) / (pad * 0.9), 0, 1)
    glow *= edge ** 2
    halo = np.dstack([glow * 1.0, glow * 0.22, glow * 0.14, np.full_like(glow, 255)]).astype(np.uint8)
    canvas = Image.alpha_composite(canvas, Image.fromarray(halo, "RGBA"))
    refl = cut.transpose(Image.FLIP_TOP_BOTTOM)
    ra = np.array(refl).astype(np.float64)
    fade = np.clip(1 - np.arange(refl.height) / (refl.height * 0.22), 0, 1) ** 1.6 * 0.22
    ra[..., 3] *= fade[:, None]
    canvas.alpha_composite(Image.fromarray(ra.astype(np.uint8), "RGBA"), (pad, pad + ch + 6))
    canvas.alpha_composite(cut, (pad, pad))
    canvas = canvas.crop((0, 0, canvas.width, pad + int(ch * 1.20)))
    cover = os.path.join(TMP, "freakout_cover_cutout.png"); canvas.convert("RGB").save(cover)
    import shutil
    os.makedirs(os.path.join(ROOT, "tools", "manual_assets"), exist_ok=True)
    for n_ in ("annotated", "knobs", "ctl", "leds", "disp", "cover_cutout"):
        shutil.copy(os.path.join(TMP, "freakout_" + n_ + ".png"), os.path.join(ROOT, "tools", "manual_assets", "freakout_" + n_ + ".png"))

# logo blanc pour la couverture (version blanche du logo officiel : lettres #FFFFFF, barre #919496)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import svg_raster
_white = os.path.join(TMP, "nine_hands_logo_blanc.svg")
open(_white, "w").write(open(os.path.join(ROOT, "NineHandsLogo.svg")).read().replace('fill="#000000"', 'fill="#FFFFFF"'))
LOGO_PNG = os.path.join(TMP, "nine_hands_logo_blanc.png")
Image.fromarray(svg_raster.render(_white, 1200)).save(LOGO_PNG)

def img(path, width):
    im = Image.open(path); h = width * im.height / im.width
    return RLImage(path, width=width, height=h)

# ---------- styles ----------
st = {
    "h1": ParagraphStyle("h1", fontName="PopB", fontSize=20, leading=24, textColor=ACC, spaceAfter=8, spaceBefore=4, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="PopM", fontSize=13, leading=17, textColor=DARK, spaceAfter=4, spaceBefore=10, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="Pop", fontSize=9.6, leading=14, textColor=DARK, spaceAfter=5),
    "small": ParagraphStyle("small", fontName="Pop", fontSize=8.2, leading=11.5, textColor=GREY),
    "cell": ParagraphStyle("cell", fontName="Pop", fontSize=8.4, leading=11, textColor=DARK),
    "cellb": ParagraphStyle("cellb", fontName="PopM", fontSize=8.4, leading=11, textColor=DARK),
    "cover": ParagraphStyle("cover", fontName="Title", fontSize=54, leading=58, textColor=colors.white, alignment=TA_CENTER),
    "coversub": ParagraphStyle("coversub", fontName="Pop", fontSize=12, leading=16, textColor=colors.HexColor("#BDBDBA"), alignment=TA_CENTER),
    "coverlang": ParagraphStyle("coverlang", fontName="PopM", fontSize=8.5, leading=11, textColor=ACC_L),
}
def P(t, s="p"): return Paragraph(t, st[s])
def bullets(items): return [P("&bull;&nbsp;&nbsp;" + i) for i in items]
def table(rows, widths, header=True):
    data = [[P(c, "cellb" if (header and r == 0) else "cell") for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#D9D9D6")),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: style += [("BACKGROUND", (0, 0), (-1, 0), LIGHT), ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACC)]
    t.setStyle(TableStyle(style)); return t

# ---------- donnees (identiques au code livre : PluginProcessor.cpp) ----------
TYPES = ["SUB", "1ST", "2ND", "3RD", "5TH", "NAT LOW", "NAT HI"]
FACTORY = [  # nom, gain, onset, type, momentary, dry
    ("Manual Setup", 5.0, 5.0, 3, 0, 1), ("Live Feedback Wail", 6.0, 4.5, 6, 0, 1), ("Studio Swell (Momentary)", 4.2, 5.8, 6, 1, 1),
    ("Unison Sustain", 5.5, 2.0, 1, 0, 1), ("Octave Scream", 7.0, 2.5, 2, 0, 1), ("Twelfth Lead", 6.0, 3.5, 3, 0, 1),
    ("Fifth Harmonic Squeal", 6.5, 3.0, 4, 0, 1), ("Sub Drone", 6.0, 6.0, 0, 0, 1), ("Minor Key Natural", 5.0, 5.0, 5, 0, 1),
    ("Doom Bloom", 7.0, 7.5, 5, 0, 1), ("EBow Swell", 6.0, 6.0, 1, 0, 0), ("Theremin Ghost", 6.5, 3.5, 3, 0, 0),
    ("Instant Squeal", 9.0, 0.5, 6, 1, 1)]
def onset_s(v):
    s = 0.03 * 200 ** (v / 10.0)
    return f"{s * 1000:.0f} ms" if s < 1 else f"{s:.1f} s"
FACT_DESC = {
 "fr": ["La procédure de réglage du manuel d'origine : GAIN, ONSET et TYPE à 12 h, footswitch à accrochage, DRY en marche.",
        "NAT HI avec un peu plus de gain : le larsen choisit lui-même son harmonique et saute de l'une à l'autre, comme un ampli à fond.",
        "Le réglage du test Tape Op (gain à 11 h, onset à 13 h, NAT HI) avec le footswitch en mode momentané.",
        "Larsen à l'unisson, montée rapide : sustain infini de la note jouée.",
        "Octave au-dessus (2e harmonique), rapide et fort : le larsen hurlant classique des solos.",
        "3e harmonique (une octave et une quinte au-dessus) : un larsen chantant, presque vocal.",
        "5e harmonique (deux octaves et une tierce majeure au-dessus) : le sifflement perçant.",
        "Octave en dessous, montée lente : un bourdon sombre sous les notes tenues.",
        "NAT LOW : larsen naturel qui ne monte jamais à la 5e harmonique, donc jamais « majeur » sur un accord mineur.",
        "NAT LOW, plus de gain et une montée très lente : d'immenses gonflements pour le doom et le post-metal.",
        "DRY coupé, unisson : la note n'apparaît qu'en gonflant, comme avec un EBow.",
        "DRY coupé, 3e harmonique : une ligne fantomatique façon thérémine au-dessus de ce que vous jouez.",
        "Gain presque à fond, montée instantanée, momentané : un coup de footswitch et le larsen part aussitôt."],
}
def pc(v): return f"{round(v * 10)} %"

T = {}
T["fr"] = dict(
 lang="FRANÇAIS", sub="Larsen naturel",
 intro_t="1. Présentation",
 intro=["<b>FreakOut</b> est un plugin VST3 NINE HANDS | DSP qui crée un larsen de guitare naturel à n'importe quel volume, en son clair ou saturé, au casque ou avec un simulateur d'ampli à faible volume. Il reprend le fonctionnement de la <b>DigiTech FreqOut</b> (Natural Feedback Creator) : mêmes commandes, mêmes sept types de larsen, même échelle de LED, mêmes inverseurs MOMENTARY et DRY.",
        "Comme la pédale, FreakOut suit la note jouée, choisit l'harmonique de cette note qui va larsener, puis la fait « fleurir » : le larsen part inaudible, grossit de façon exponentielle tant que la note tient, puis sature en douceur. Il suit le vibrato, les tirés et le legato, retombe quand on étouffe les cordes et se reconstruit à chaque nouvelle attaque.",
        "La pédale est entièrement numérique et aucun schéma n'existe : FreakOut a été construit d'après le manuel d'origine, les tests (Sound On Sound, MusicRadar, Tape Op, Guitar Interactive) et le comportement documenté de chaque commande."],
 inst_t="2. Installation",
 inst=[("Windows", "Copiez <b>FreakOut.vst3</b> dans <b>C:\\Program Files\\Common Files\\VST3</b>. Dans Reaper : Options &gt; Preferences &gt; Plug-ins &gt; VST &gt; <i>Re-scan</i>. Le plugin apparaît sous le nom <b>FreakOut (NINE HANDS | DSP)</b>."),
       ("macOS", "Décompressez l'archive et copiez <b>FreakOut.vst3</b> dans <b>/Library/Audio/Plug-Ins/VST3</b> (ou ~/Library/Audio/Plug-Ins/VST3). La version est universelle (Apple Silicon et Intel) et signée localement ; si macOS la bloque, lancez <i>xattr -cr</i> sur le fichier. Relancez ensuite le scan dans Reaper.")],
 ov_t="3. Vue d'ensemble",
 ov_rows=[["N°", "Commande", "Rôle"], ["1", "Échelle FEEDBACK", "9 LED rouges : centre = effet actif ; les paires s'allument du centre vers l'extérieur pendant la montée du larsen"],
          ["2", "MOMENTARY", "On : larsen seulement tant que le footswitch est enfoncé. Off : footswitch à accrochage"],
          ["3", "DRY", "On : guitare + larsen. Off : larsen seul (effet de gonflement)"],
          ["4", "RANGE – GAIN", "Chapeau central du potard concentrique : quantité de larsen"],
          ["5", "RANGE – ONSET", "Jupe moletée : temps pour que le larsen atteigne sa pleine intensité"],
          ["6", "TYPE", "Harmonique qui larsène : SUB, 1ST, 2ND, 3RD, 5TH, NAT LOW, NAT HI"],
          ["7", "Écran", "Valeur de la commande touchée, sinon l'harmonique, la fréquence et la note qui larsènent"],
          ["8", "Barre de presets", "Flèches = preset précédent / suivant, nom = menu des presets"],
          ["9", "Footswitch", "Effet en marche / coupé (ou maintenu, en mode momentané)"],
          ["10 / 11", "OUT / IN", "Sortie à gauche, entrée à droite, comme sur une vraie pédale"]],
 ctl_t="4. Les commandes",
 ctl=[("RANGE – GAIN (chapeau central)", "Règle le volume que prend le larsen, par rapport à l'attaque de la note jouée : de rien à environ +6 dB au-dessus de l'attaque. À 12 h, le larsen se stabilise un peu sous le niveau de l'attaque. Plus haut, on gagne en sustain et le haut de la montée devient un peu plus riche et saturé."),
      ("RANGE – ONSET (jupe)", "Règle le temps que met le larsen pour atteindre sa pleine intensité : 30 ms tout à gauche, environ 0,4 s à 12 h, 6 s tout à droite. La croissance est exponentielle, comme un vrai larsen : rien pendant un instant, puis un gonflement rapide. Tirez le chapeau pour GAIN et la jupe pour ONSET ; double-clic = retour à 12 h, Maj = réglage fin."),
      ("TYPE", "Choisit l'harmonique qui larsène. Une harmonique est un multiple de la fréquence de la note : <b>1ST</b> = unisson, <b>2ND</b> = octave au-dessus, <b>3RD</b> = octave + quinte, <b>5TH</b> = deux octaves + tierce majeure, <b>SUB</b> = octave en dessous (sur les notes trop graves pour être entendues une octave plus bas, il repasse à l'unisson). <b>NAT LOW</b> et <b>NAT HI</b> se comportent comme un larsen naturel : l'harmonique dépend de ce qui sonne réellement dans la corde, la même note peut donc larsener différemment à chaque fois. NAT LOW reste dans les harmoniques basses (jamais la 5e ni au-dessus, donc pas de tierce majeure sur un accord mineur) ; NAT HI monte plus haut et saute plus volontiers d'un partiel à l'autre, en redescendant en général quand la note s'éteint. Tourner TYPE pendant que ça larsène fait passer le larsen sur la nouvelle harmonique."),
      ("Orienter les types naturels", "Comme sur la pédale : jouez plus doucement, baissez la tonalité ou prenez le micro manche pour un larsen plus grave ; attaquez plus fort, ouvrez la tonalité ou prenez le micro chevalet pour un larsen plus aigu."),
      ("DRY", "On : la guitare passe, le larsen s'ajoute par-dessus. Off : quand l'effet est en marche, on n'entend que le larsen, chaque note arrive donc en gonflant depuis le silence, comme avec un EBow ou un thérémine. Effet coupé, le signal sec passe toujours.")],
 knobs_cap="RANGE (chapeau GAIN au centre, jupe ONSET autour) et TYPE : seuls les repères crème tournent, reflets et moletage restent fixes.",
 fs_t="5. Footswitch, LED et modes",
 fs=["<b>Footswitch</b> : un clic met l'effet en marche ou le coupe ; le bouton descend dans son écrou tant qu'on appuie. Avec <b>MOMENTARY ON</b>, l'effet n'agit que tant que le bouton de la souris (ou le footswitch MIDI) est maintenu. Enclencher l'effet pendant qu'une note sonne fait partir le larsen de cette note.",
     "<b>Échelle de LED</b> : la LED du centre indique que l'effet est en marche ; les autres s'allument par paires du centre vers l'extérieur pendant que le larsen monte : l'échelle montre la montée en temps réel. La lumière des LED éclaire la façade autour d'elles.",
     "<b>Sensibilité de déclenchement</b> (menu clic droit) : Low pour les micros puissants ou une pièce bruyante, Normal, High pour les micros faibles et un jeu léger.",
     "Tous les paramètres sont automatisables dans le DAW (Gain, Onset, Type, Momentary, Dry, Effect On, ainsi que la sensibilité de déclenchement et le mode du footswitch MIDI)."],
 midi_t="6. MIDI",
 midi_txt=["<b>MIDI Learn sur toutes les commandes</b> : faites un clic droit sur une commande (chapeau GAIN, jupe ONSET, TYPE, MOMENTARY, DRY ou le footswitch). Le haut du menu affiche <b>MIDI Learn: &lt;Nom&gt; (CC n / none)</b> avec l'assignation actuelle, <b>Clear MIDI: &lt;Nom&gt;</b> et, tant qu'un apprentissage est en attente, <b>Cancel MIDI learn</b>. Choisissez MIDI Learn puis bougez une pédale, un bouton ou appuyez sur un footswitch de votre contrôleur : l'écran affiche <b>MIDI LEARN: move a control for &lt;Nom&gt;</b>, puis <b>&lt;Nom&gt; = CC n</b> pendant 2 secondes.",
           "Aucun CC n'est assigné par défaut : chaque commande à piloter en MIDI s'assigne avec le MIDI Learn. Chaque menu clic droit (sur une commande ou ailleurs sur la pédale) contient aussi le sous-menu <b>MIDI map</b> : <b>Learn</b> pour chacune des 6 commandes (avec son assignation actuelle, ou <b>none</b>), <b>Cancel MIDI learn</b> et <b>Clear all MIDI assignments</b>, qui efface toutes les assignations, plus un rappel de la réaction des commandes. Choisir de nouveau la commande en attente annule aussi l'apprentissage.",
           "Un numéro de CC ne pilote qu'une seule commande : apprendre un CC déjà utilisé le retire de l'autre commande. L'apprentissage accepte les CC 0 à 119 ; FreakOut écoute tous les canaux MIDI. <b>Les assignations sont sauvegardées avec le projet</b> (et avec les presets du DAW). Un projet fait avec une version précédente qui utilisait encore les anciens numéros d'usine (CC 20 à 25) s'ouvre sans aucune assignation : réapprenez les commandes voulues. Un projet où vous aviez changé une assignation garde ses assignations telles qu'enregistrées."],
 midi_hdr=["Commande", "Type"],
 midi=[["Gain (chapeau GAIN)", "Continu 0-127 ; 14 bits avec CC n+32 si le CC appris est entre 0 et 31"], ["Onset (jupe ONSET)", "Continu 0-127 ; 14 bits avec CC n+32 si le CC appris est entre 0 et 31"],
       ["Type", "Sélecteur à 7 positions : 0-127 découpé en 7 zones égales (SUB à NAT HI)"],
       ["Momentary", "Bascule : 64 et plus = ON, moins de 64 = OFF"], ["Dry", "Bascule : 64 et plus = ON, moins de 64 = OFF"],
       ["Footswitch", "Footswitch : à accrochage (127 = on / 0 = off) ou bascule à chaque appui ; avec MOMENTARY ON, il agit tant qu'il est enfoncé"]],
 midi2=["<b>Mode du footswitch MIDI</b> : clic droit &gt; <b>Settings</b> &gt; <b>MIDI footswitch latching (127 = on / 0 = off)</b> (par défaut) ou <b>MIDI footswitch toggles on each press</b>. Avec MOMENTARY ON, le footswitch MIDI agit toujours tant qu'il est enfoncé.",
        "<b>Pédales d'expression</b> sur GAIN ou ONSET : mouvement lissé (rampe entre deux messages), CC 14 bits accepté, course de la pédale apprise automatiquement et petites zones mortes aux deux butées.",
        "<b>Program Change</b> 1 à 13 : presets d'usine."],
 ctl_cap="Inverseurs MOMENTARY / DRY (levier en haut = ON), et footswitch relâché / enfoncé.",
 led_cap="L'échelle de LED : effet en marche (LED centrale), bypass, larsen qui monte, larsen à pleine intensité.",
 win_t="7. Fenêtre et écran",
 win=["Clic droit &gt; <b>Plugin size</b> : <b>60 %</b>, <b>75 %</b>, <b>100 %</b> redimensionne cette fenêtre, et <b>(default)</b> est indiqué à côté de la taille par défaut choisie. En bas du même menu, <b>Default size (new windows)</b> choisit la taille d'ouverture de toutes les nouvelles fenêtres de FreakOut (réglage commun à toutes les instances, enregistré sur l'ordinateur) ; la fenêtre ouverte prend aussitôt cette taille. La fenêtre ne peut jamais être réduite sous 60 % ; on peut aussi tirer le coin pour l'agrandir jusqu'à 150 % (proportions bloquées).",
      "L'écran affiche pendant 2,5 s la valeur de la commande que vous venez de bouger. Le reste du temps, il montre ce qui larsène : harmonique (H1, H2… ou SUB), fréquence et nom de la note. La barre de presets dessous fonctionne comme un menu de pédale : flèches pour précédent / suivant, clic sur le nom pour la liste complète (presets d'usine, 9 emplacements utilisateur à charger ou enregistrer)."],
 disp_cap="Écran : informations du larsen en direct, puis valeur de la commande qu'on règle.",
 pre_t="8. Presets",
 pre=["13 presets d'usine sont fournis (aussi dans le menu de presets du DAW et en Program Change MIDI). Neuf emplacements utilisateur peuvent être enregistrés depuis le menu des presets."],
 fac_hdr=["N°", "Preset", "Gain / Onset", "Type", "Inverseurs", "Description"],
 tips_t="9. Conseils d'utilisation",
 tips=["Dans Reaper, placez FreakOut en premier dans la chaîne, avant Ampire ou tout simulateur d'ampli, comme le recommande le manuel d'origine : il a besoin du signal clair de la guitare pour lire les harmoniques. Un compresseur ou un buffer avant lui ne pose pas de problème.",
       "Étouffez les cordes que vous ne jouez pas : comme pour un vrai larsen, des cordes qui sonnent à vide rendent le larsen moins prévisible.",
       "Apprenez GAIN ou ONSET sur une pédale d'expression pour doser le larsen au pied, comme en s'approchant de l'ampli.",
       "Accordages graves : la détection descend jusqu'à 30 Hz, une 7 cordes en G (49 Hz) ou plus bas fonctionne. Sur les notes très graves, 2ND ou 3RD donnent en général le larsen le plus audible ; SUB repasse à l'unisson sous environ 50 Hz.",
       "Pour des lignes façon EBow / thérémine : DRY coupé, 1ST ou 3RD, onset vers 13 h, puis delay et reverb après le simulateur d'ampli.",
       "Pour le larsen « ampli à fond » sur les notes tenues : NAT HI, gain à 13 h, onset à 11 h, MOMENTARY ON, et appuyez quand la note doit hurler."],
 tech_t="10. Caractéristiques techniques",
 tech=[["Format", "VST3, Windows (x64) et macOS (Apple Silicon + Intel)"], ["Canaux", "Mono ou stéréo (la détection utilise la somme des canaux)"],
       ["Latence", "Aucune (0 échantillon)"], ["Plage de hauteur", "Fondamentale de 30 Hz à 1,6 kHz, larsen jusqu'à 8,5 kHz"],
       ["Moteur", "Détection de hauteur YIN, oscillateurs harmoniques verrouillés en phase, montée exponentielle, choix naturel des partiels"],
       ["Fréquences", "44,1 à 192 kHz"],        ["Fenêtre", "60 % / 75 % / 100 % (Plugin size), taille par défaut des nouvelles fenêtres au choix, jusqu'à 150 %, jamais sous 60 % ; anti-gel v2 sous Windows (rendu logiciel, caches d'affichage refaits par un timer, chien de garde de redessin, aucun appel à l'hôte depuis le thread audio)"],
       ["MIDI", "MIDI Learn sur les 6 commandes (sauvegardé avec le projet), aucun CC assigné par défaut, CC 14 bits (n+32), Program Change 1 à 13, tous canaux"]],
)

W = A4[0] - 36 * mm
def section(lang):
    t = T[lang]; f = []
    COVER_TEXT.update(lang=t["lang"], sub=t["sub"])
    f.append(NextPageTemplate("p"))
    f.append(Spacer(1, 1))                       # couverture : tout est dessine par cover_bg (gabarit fixe)
    f.append(PageBreak())
    f.append(P(t["intro_t"], "h1")); f += [P(x) for x in t["intro"]]
    f.append(P(t["inst_t"], "h1"))
    for h, x in t["inst"]: f.append(P(h, "h2")); f.append(P(x))
    f.append(PageBreak())
    f.append(P(t["ov_t"], "h1"))
    ov = Table([[img(annotated, 92 * mm), table(t["ov_rows"], [11 * mm, 25 * mm, W - 96 * mm - 36 * mm])]], colWidths=[96 * mm, W - 96 * mm])
    ov.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    f.append(ov)
    f.append(PageBreak())
    f.append(P(t["ctl_t"], "h1"))
    for h, x in t["ctl"]: f.append(P(h, "h2")); f.append(P(x))
    f.append(KeepTogether([Spacer(1, 3 * mm), img(knobs_img, W * 0.46), P(t["knobs_cap"], "small")]))
    f.append(P(t["fs_t"], "h1")); f += bullets(t["fs"])
    f.append(KeepTogether([Spacer(1, 2 * mm), img(ctl_img, W * 0.66), P(t["ctl_cap"], "small")]))
    f.append(KeepTogether([Spacer(1, 3 * mm), img(leds_img, W * 0.42), P(t["led_cap"], "small")]))
    f.append(P(t["midi_t"], "h1")); f += [P(x) for x in t["midi_txt"]]
    f.append(Spacer(1, 2 * mm)); f.append(KeepTogether([table([t["midi_hdr"]] + t["midi"], [40 * mm, W - 40 * mm])])); f.append(Spacer(1, 3 * mm))
    f += bullets(t["midi2"])
    f.append(P(t["win_t"], "h1")); f += [P(x) for x in t["win"]]
    f.append(KeepTogether([img(disp_img, W * 0.92), P(t["disp_cap"], "small")]))
    f.append(CondPageBreak(150 * mm))
    f.append(P(t["pre_t"], "h1")); f += [P(x) for x in t["pre"]]
    rows = [t["fac_hdr"]]
    for i, (n, g, o, ty, mo, dr_) in enumerate(FACTORY):
        sw = ("MOM " + ("on" if mo else "off")) + " · DRY " + ("on" if dr_ else "off")
        rows.append([str(i + 1), "<b>" + n + "</b>", f"{pc(g)} / {pc(o)}<br/>({onset_s(o)})", TYPES[ty], sw, FACT_DESC[lang][i]])
    f.append(table(rows, [9 * mm, 30 * mm, 22 * mm, 16 * mm, 22 * mm, W - 99 * mm]))
    f.append(PageBreak())
    f.append(P(t["tips_t"], "h1")); f += bullets(t["tips"])
    f.append(KeepTogether([P(t["tech_t"], "h1"), table(t["tech"], [32 * mm, W - 32 * mm], header=False)]))
    f.append(PageBreak())
    return f

def deco(c, doc):
    c.saveState()
    c.setFillColor(DARK); c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, A4[1] - 6.8 * mm, A4[0], 0.8 * mm, stroke=0, fill=1)
    c.setFont("Pop", 7.5); c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "FreakOut (NINE HANDS | DSP) · v" + VERSION)
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, str(doc.page))
    c.restoreState()

doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=18 * mm,
                      title="FreakOut - Notice v" + VERSION, author="NINE HANDS | DSP")
# ---- Couverture « minimale » (modele 6, valide nov. 2026) : gabarit fixe commun a toutes les notices ----
# Mesures en mm depuis le HAUT de la page A4, sauf le logo et le bandeau (depuis le bas). Aucun autre element.
COVER_TEXT = {}
COVER_NAME = "FREAKOUT"
PEDAL_H, PEDAL_MAXW, PEDAL_TOP = 82 * mm, 115 * mm, 84 * mm
LANG_TOP = 18 * mm
NAME_TOP, NAME_PT = 194 * mm, 30
SUB_TOP, SUB_PT = 208 * mm, 10
LOGO_W, LOGO_BOTTOM = 38 * mm, 22 * mm
BAND_H = 3 * mm
def cover_bg(c, doc):
    c.saveState(); c.setFillColor(colors.black); c.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)
    c.setFillColor(ACC); c.rect(0, 0, A4[0], BAND_H, stroke=0, fill=1)
    def line(text, top, font, size, cs, col):
        w = pdfmetrics.stringWidth(text, font, size) + cs * (len(text) - 1)
        tx = c.beginText((A4[0] - w) / 2, A4[1] - top - size * 0.8); tx.setFont(font, size); tx.setCharSpace(cs)
        tx.setFillColor(col); tx.textOut(text); c.drawText(tx)
    line(COVER_TEXT["lang"], LANG_TOP, "PopM", 8.5, 0, ACC_L)
    ci = Image.open(cover); iw, ih = ci.size
    cw = iw / 1.32; ch = (ih - int(cw * 0.16)) / 1.2; pad = int(cw * 0.16)     # geometrie de freakout_cover_cutout.png
    k = min(PEDAL_H / ch, PEDAL_MAXW / cw)
    dw, dh = iw * k, ih * k
    y0 = A4[1] - (PEDAL_TOP + (PEDAL_H - ch * k) / 2) + pad * k
    c.drawImage(cover, (A4[0] - dw) / 2, y0 - dh, dw, dh)
    line(COVER_NAME, NAME_TOP - NAME_PT * 0.02, "Title", NAME_PT, NAME_PT * 0.5, colors.white)
    line(COVER_TEXT["sub"], SUB_TOP, "Pop", SUB_PT, 1.5, colors.HexColor("#BDC4B8"))
    lw, lh = Image.open(LOGO_PNG).size
    c.drawImage(LOGO_PNG, (A4[0] - LOGO_W) / 2, LOGO_BOTTOM, LOGO_W, LOGO_W * lh / lw, mask="auto")
    c.restoreState()
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="fc")], onPage=cover_bg),
                      PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")], onPage=deco)])
fr = section("fr")              # notice en francais uniquement (couverture noire FRANCAIS)
doc.build(fr[:-1])
print(OUT)
