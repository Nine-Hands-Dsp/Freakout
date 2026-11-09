# FreakOut (NINE HANDS | DSP)

Plugin VST3 (Windows et macOS) de **larsen naturel** pour guitare et basse, au format pédale simple,
d'après le fonctionnement de la DigiTech FreqOut (Natural Feedback Creator). Visuel original NINE HANDS | DSP.

<p align="center">
  <a href="https://github.com/Nine-Hands-Dsp/Freakout/releases/latest/download/FreakOut-VST3-Windows.zip"><img alt="Télécharger pour Windows" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-Windows-0078D6?style=for-the-badge"></a>
  <a href="https://github.com/Nine-Hands-Dsp/Freakout/releases/latest/download/FreakOut-VST3-macOS.zip"><img alt="Télécharger pour macOS" src="https://img.shields.io/badge/%E2%AC%87%20T%C3%A9l%C3%A9charger-macOS-111111?style=for-the-badge&logo=apple&logoColor=white"></a>
  <br>
  <a href="https://github.com/Nine-Hands-Dsp/Freakout/releases/latest"><img alt="Dernière version" src="https://img.shields.io/github/v/release/Nine-Hands-Dsp/Freakout?label=derni%C3%A8re%20version&color=919496"></a>
</p>

## Commandes (comme la pédale d'origine)

| Commande | Rôle |
|---|---|
| **RANGE – GAIN** (chapeau central) | quantité de larsen (relative à l'attaque de la note), de rien à +6 dB |
| **RANGE – ONSET** (jupe moletée) | temps pour que le larsen atteigne sa pleine intensité : 30 ms à 6 s (12 h ≈ 0,4 s) |
| **TYPE** | SUB (octave en dessous), 1ST (unisson), 2ND, 3RD, 5TH (n × la fréquence de la note), NAT LOW, NAT HI |
| **MOMENTARY** | ON : le larsen n'agit que tant que le footswitch est enfoncé ; OFF : footswitch à accrochage |
| **DRY** | ON : la guitare reste ; OFF : larsen seul (gonflement façon EBow / thérémine) |
| **Échelle FEEDBACK** | LED centrale = effet actif ; les paires s'allument du centre vers l'extérieur pendant la montée du larsen |
| **Écran** | valeur du réglage touché (2,5 s), sinon l'harmonique qui larsène (ex. « H3 247 Hz B3 ») ; barre de presets |

NAT LOW n'utilise jamais la 5e harmonique ou au-dessus (pas de tierce majeure sur les accords mineurs) ;
NAT HI explore des partiels plus aigus et bascule plus volontiers d'un partiel à l'autre. Comme sur la pédale,
le choix dépend de l'attaque, du micro et de la tonalité : attaque forte + micro chevalet = larsen plus aigu.

## Moteur sonore (`FreakoutDSP.h`)

1. Détection de hauteur YIN sur signal décimé (~12 kHz), de 30 Hz (7 cordes en G grave, basse) à 1,6 kHz.
2. Choix de l'harmonique selon TYPE ; en NAT, score par partiel (énergie réelle dans la corde × courbe de
   résonance de la boucle × un peu de hasard par note) avec hystérésis, le centre de résonance descendant
   quand la note vieillit (les aigus s'éteignent d'abord, comme un vrai larsen).
3. Le partiel est isolé (passe-bande d'état), son signal analytique (paire de passe-tout en quadrature)
   pilote une PLL : l'oscillateur reste **en phase** avec la corde (vibrato, tirés, inharmonicité), puis
   « gonfle » de façon exponentielle (linéaire en dB, de −40 à +6 dB virtuels, saturation douce en haut) ;
   2e/3e harmoniques et micro-respiration apparaissent quand il sature.
4. Attaque de médiator = le larsen en cours est coupé et se reconstruit ; corde étouffée (> 18 dB en 80 ms)
   = il retombe en 70 ms ; legato / glissando = il glisse vers la nouvelle note sans clic.
5. Aucune latence, aucune allocation ni verrou dans le thread audio.

## MIDI

Aucun CC assigné par défaut : clic droit > MIDI > Learn (Gain, Onset (CC n+32 en 14 bits), Type, Momentary, Dry, footswitch).
Program Change 1-13 = presets d'usine. Pédale d'expression : rampe sans saccade, course apprise automatiquement.
MOMENTARY ON : le footswitch MIDI agit tant qu'il est enfoncé.

**MIDI Learn (v1.1)** : clic droit sur une commande (chapeau GAIN, jupe ONSET, TYPE, MOMENTARY, DRY, footswitch)
> « MIDI Learn: <commande> », puis bouger la pédale / appuyer sur le footswitch MIDI ; l'afficheur indique
« MIDI LEARN: move a control for … » puis « <commande> = CC n ». « Clear MIDI » retire l'assignation,
clic droit > MIDI map > « Clear all MIDI assignments » efface toutes les assignations. Assignations sauvegardées avec le projet.

## Fenêtre

Pédale plein cadre (fond 1235 × 1800 px), hauteur par défaut 493 px (338 × 493), impossible de la réduire en dessous ; clic droit : **Plugin size**
(60 / 75 / 100 %, la taille par défaut marquée « (default) » ; **Default size (new windows)** choisit la taille
d'ouverture des nouvelles fenêtres, commune à toutes les instances, et redimensionne aussi la fenêtre courante), presets, sensibilité de déclenchement, mode du footswitch MIDI, table MIDI.

**Anti-gel v2** : rendu logiciel forcé sous Windows, aucun calcul lourd dans `paint()`, caches reconstruits
par le timer, chien de garde de redessin, aucun appel à l'hôte depuis le thread audio.

## Construction

JUCE 8.0.15 + CMake ; GitHub Actions (`windows-2022`, `macos-14`) produit les VST3 prêts à installer.
Visuel : `python3 tools/make_art.py` (≈ 20 s) : boîtier et cadre calculés en 4K (4 px par unité) puis ramenés en 1235 × 1800,
kit photo NINE HANDS | DSP (potards, LED, footswitch, jacks, inverseurs), transparence seulement autour des jacks ;
génère aussi `Layout.h` et `tools/layout.json`. Textes, traits, points, cadre et logo (`NineHandsLogo.svg`) sont
dessinés en vectoriel par l'éditeur, nets à toutes les tailles.
Captures réelles : `tools/render` (compile la vraie fenêtre sous Linux).
Polices : Poppins (interface) et Barlow Condensed (notice), licence SIL OFL, `assets/fonts`.
Notice : `python3 tools/manual.py design/renders docs/FreakOut_Notice_FR_v1.3.5.pdf` (français).

- v1.0.2 : menu de taille de fenêtre : « 60 % (default) », 75 %, 100 % (plus de taille en pixels)
- v1.1.0 : MIDI Learn au clic droit sur chaque commande (Clear MIDI, assignations sauvegardées avec le projet)
- v1.2.0 : clic droit > Plugin size > Default size (new windows) : taille par défaut des nouvelles fenêtres au choix, comme dans Octopus
- v1.2.1 : plus aucun CC MIDI assigné par défaut (tout passe par le MIDI Learn)
- v1.2.2 : boutons de téléchargement dans le README
- v1.3.0 : pédale entièrement refaite au format 1235 × 1800 avec le kit photo (potards, LED, footswitch, jacks, inverseurs), sérigraphie et cadre vectoriels, menus clic droit au design d'Octopus, notice en français
- v1.3.1 : texture d'aluminium brossé fournie par l'utilisateur, plus d'ombre autour du jack OUT, lumière des LED +10 %, colonnes FEEDBACK et MOMENTARY / DRY alignées sur l'écran, titre et sous-titre centrés à l'encre et de même largeur, plus de disque clair autour du footswitch
- v1.3.2 : nouvelle texture d'aluminium brossé en une seule plaque haute résolution (sans raccord ni pixellisation), nouveau footswitch (photo de l'utilisateur)
- v1.3.3 : contraste de la texture brossée réduit de 20 %
- v1.3.3 : contraste de la texture brossée réduit de 20 %
- v1.3.4 : les menus clic droit s'ouvrent toujours à l'endroit du clic
- v1.3.5 : logo NINE HANDS | DSP entièrement noir (fichier v003 de l'utilisateur), MOMENTARY plus compact, filets sous MOMENTARY et DRY de la largeur du mot
