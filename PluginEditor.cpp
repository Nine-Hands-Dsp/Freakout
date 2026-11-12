#include "PluginEditor.h"
#include "BinaryData.h"
#include "Layout.h"
#include "WigaWindowSize.h"

using namespace juce;

namespace
{
    // repere 617,5 x 900 (fond 1235 x 1800 px / 2), positions generees par tools/make_art.py dans Layout.h
    const Rectangle<float> statusRect = layout::statusRect;
    const Rectangle<float> presetRect = layout::presetRect;

    const float rotStart = -150.0f, rotEnd = 150.0f;    // degres, 0 = midi (repere vers le haut)
    float knobAngle (float v) { return degreesToRadians (rotStart + (rotEnd - rotStart) * jlimit (0.0f, 10.0f, v) / 10.0f); }

    const Colour inkDark (0xff1b1b1e), inkLight (0xffdcdcd8);      // serigraphie : noire sur le metal, claire sur les panneaux
    const Colour lcd (0xffe9b48f), presetInk (0xffd6d6d4);           // ecran : ambre, barre de presets
    const Colour pointerCream (0xffe8e1d4);                          // repere creme des potards (comme la photo)

    const char* const valueIds[] = { "gain", "onset", "type", "momentary", "dry", "active", "sensitivity" };
    constexpr int numValueIds = 7;

    // repere creme sur le dessus d'un potard (vue de dessus) : de f0 a f1 du rayon, bouts arrondis ;
    // lumiere en haut a gauche : fine ombre vers le bas a droite, peinture un peu plus claire tournee vers la lumiere
    void paintPointer (Graphics& g, Point<float> c, float R, float a, float f0, float f1, float w)
    {
        const Point<float> dir (std::sin (a), -std::cos (a));
        Path line; line.startNewSubPath (c + dir * (f0 * R)); line.lineTo (c + dir * (f1 * R));
        g.setColour (Colours::black.withAlpha (0.55f));
        g.strokePath (line, PathStrokeType (w * 1.12f, PathStrokeType::curved, PathStrokeType::rounded), AffineTransform::translation (R * 0.012f, R * 0.018f));
        const float lightFacing = 0.5f + 0.5f * std::cos (a + MathConstants<float>::pi * 0.25f);
        g.setColour (pointerCream.withMultipliedBrightness (0.93f + 0.07f * lightFacing));
        g.strokePath (line, PathStrokeType (w, PathStrokeType::curved, PathStrokeType::rounded));
    }
}

//==============================================================================
// POTARD CONCENTRIQUE RANGE
//==============================================================================
ConcentricKnob::ConcentricKnob (RangedAudioParameter& g, RangedAudioParameter& o)
    : gainAtt  (g, [this] (float v) { gainV = v;  if (onValue) onValue(); }),
      onsetAtt (o, [this] (float v) { onsetV = v; if (onValue) onValue(); })
{
    gainAtt.sendInitialUpdate();
    onsetAtt.sendInitialUpdate();
    setMouseCursor (MouseCursor::PointingHandCursor);
}

bool ConcentricKnob::hitTest (int x, int y)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    return c.getDistanceFrom ({ (float) x, (float) y }) <= (float) getWidth() * 0.5f;
}

int ConcentricKnob::zoneAt (Point<float> p) const
{
    const auto c = getLocalBounds().toFloat().getCentre();
    const float unit = (float) getWidth() * 0.5f / layout::skirtR;
    return c.getDistanceFrom (p) <= (layout::capR + 2.0f) * unit ? 0 : 1;      // chapeau GAIN au centre, jupe ONSET autour
}

void ConcentricKnob::setV (int which, float v)
{
    v = jlimit (0.0f, 10.0f, v);
    if (which == 0) gainAtt.setValueAsPartOfGesture (v);
    else            onsetAtt.setValueAsPartOfGesture (v);
    if (onUserChange) onUserChange();
    if (onTouched) onTouched (which);
}

void ConcentricKnob::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { rightZone = zoneAt (e.position); if (onRightClick) onRightClick(); return; }
    dragging = zoneAt (e.position);
    startV = valueOf (dragging);
    if (dragging == 0) gainAtt.beginGesture(); else onsetAtt.beginGesture();
    if (onTouched) onTouched (dragging);
}

void ConcentricKnob::mouseDrag (const MouseEvent& e)
{
    if (dragging < 0) return;
    const float sens = e.mods.isShiftDown() ? 900.0f : 220.0f;     // Maj = reglage fin
    const float d = (float) (e.getDistanceFromDragStartX() - e.getDistanceFromDragStartY());
    setV (dragging, startV + d * 10.0f / sens);
}

void ConcentricKnob::mouseUp (const MouseEvent&)
{
    if (dragging == 0) gainAtt.endGesture(); else if (dragging == 1) onsetAtt.endGesture();
    dragging = -1;
}

void ConcentricKnob::mouseDoubleClick (const MouseEvent& e)
{
    const int z = zoneAt (e.position);
    if (z == 0) gainAtt.setValueAsCompleteGesture (5.0f); else onsetAtt.setValueAsCompleteGesture (5.0f);
    if (onUserChange) onUserChange();
    if (onTouched) onTouched (z);
}

void ConcentricKnob::mouseWheelMove (const MouseEvent& e, const MouseWheelDetails& w)
{
    const int z = zoneAt (e.position);
    const float v = valueOf (z) + (w.deltaY > 0 ? 0.2f : -0.2f) * (e.mods.isShiftDown() ? 0.25f : 1.0f);
    if (z == 0) gainAtt.setValueAsCompleteGesture (jlimit (0.0f, 10.0f, v));
    else        onsetAtt.setValueAsCompleteGesture (jlimit (0.0f, 10.0f, v));
    if (onUserChange) onUserChange();
    if (onTouched) onTouched (z);
}


//==============================================================================
// SELECTEUR TYPE
//==============================================================================
TypeKnob::TypeKnob (RangedAudioParameter& p)
    : attachment (p, [this] (float v)
                  {
                      pos = jlimit (0, 6, roundToInt (v));
                      targetAngle = degreesToRadians (-135.0f + 45.0f * (float) pos);
                  })
{
    attachment.sendInitialUpdate();
    shownAngle = targetAngle;
    setMouseCursor (MouseCursor::PointingHandCursor);
}

bool TypeKnob::hitTest (int x, int y)
{
    const auto c = getLocalBounds().toFloat().getCentre();
    return c.getDistanceFrom ({ (float) x, (float) y }) <= (float) getWidth() * 0.5f;
}

void TypeKnob::moveTo (int p)
{
    p = jlimit (0, 6, p);
    if (p == pos) return;
    attachment.setValueAsCompleteGesture ((float) p);
    if (onUserChange) onUserChange();
}

void TypeKnob::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick(); return; }
    dragStartPos = pos;
}

void TypeKnob::mouseDrag (const MouseEvent& e)
{
    const int d = (e.getDistanceFromDragStartX() - e.getDistanceFromDragStartY()) / 24;
    moveTo (dragStartPos + d);
}

void TypeKnob::mouseWheelMove (const MouseEvent&, const MouseWheelDetails& w)
{
    if (std::abs (w.deltaY) > 0.0f) moveTo (pos + (w.deltaY > 0 ? 1 : -1));
}

bool TypeKnob::tick()
{
    // le selecteur tourne d'un cran a l'autre en ~70 ms (pas de saut)
    if (std::abs (targetAngle - shownAngle) < 0.002f)
    {
        if (std::abs (shownAngle - targetAngle) > 0.0f) { shownAngle = targetAngle; return true; }
        return false;
    }
    shownAngle += (targetAngle - shownAngle) * 0.55f;
    return true;
}


//==============================================================================
// INVERSEUR (haut = ON)
//==============================================================================
LeverSwitch::LeverSwitch (RangedAudioParameter& p)
    : attachment (p, [this] (float v)
                  {
                      const bool nv = v > 0.5f;
                      if (nv != on)
                      {
                          on = nv;
                          targetFrame = on ? 0 : 2;
                          shownFrame = 1;                                   // position intermediaire ~55 ms
                          transitionUntil = Time::getMillisecondCounterHiRes() + 55.0;
                          repaint();
                      }
                  })
{
    attachment.sendInitialUpdate();
    targetFrame = shownFrame = on ? 0 : 2;
    setMouseCursor (MouseCursor::PointingHandCursor);
}

void LeverSwitch::tick (double now)
{
    if (shownFrame != targetFrame && now >= transitionUntil) { shownFrame = targetFrame; repaint(); }
}

void LeverSwitch::paint (Graphics& g)
{
    if (! strip.isValid()) return;
    const int fw = strip.getWidth(), fh = strip.getHeight() / 3;
    g.setImageResamplingQuality (Graphics::highResamplingQuality);
    g.drawImage (strip, 0, 0, getWidth(), getHeight(), 0, shownFrame * fh, fw, fh);
}

bool LeverSwitch::hitTest (int x, int y)
{
    // rondelle et levier (le sprite contient aussi l'ombre portee)
    const auto b = getLocalBounds().toFloat();
    return std::abs ((float) x - b.getCentreX()) < b.getWidth() * 0.26f && std::abs ((float) y - b.getCentreY()) < b.getHeight() * 0.38f;
}

void LeverSwitch::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick(); return; }
    attachment.setValueAsCompleteGesture (on ? 0.0f : 1.0f);
    if (onUserChange) onUserChange();
}

void LeverSwitch::mouseWheelMove (const MouseEvent&, const MouseWheelDetails& w)
{
    if (std::abs (w.deltaY) < 0.001f) return;
    const bool want = w.deltaY > 0;      // molette vers le haut = levier en haut (ON)
    if (want != on) { attachment.setValueAsCompleteGesture (want ? 1.0f : 0.0f); if (onUserChange) onUserChange(); }
}

//==============================================================================
// FOOTSWITCH
//==============================================================================
FootSwitchArea::FootSwitchArea (RangedAudioParameter& p, std::atomic<float>* momentary)
    : mom (momentary),
      attachment (p, [this] (float v) { value = v > 0.5f; repaint(); })
{
    attachment.sendInitialUpdate();
    setMouseCursor (MouseCursor::PointingHandCursor);
}

bool FootSwitchArea::hitTest (int x, int y)
{
    // zone d'appui circulaire : le bouton et l'ecrou (le sprite contient aussi l'ombre)
    const auto c = getLocalBounds().toFloat().getCentre();
    return c.getDistanceFrom ({ (float) x, (float) y }) <= (float) getWidth() * (layout::footR * 1.45f / layout::fsS);
}

void FootSwitchArea::paint (Graphics& g)
{
    if (! pressed) return;
    const auto b = getLocalBounds().toFloat();
    // bouton enfonce dans son ecrou (sprite au meme cadrage que le footswitch du fond)
    if (down.isValid())
    {
        g.setImageResamplingQuality (Graphics::highResamplingQuality);
        g.drawImage (down, b);
    }
    // et assombri tant qu'on appuie (disque noir a 25 %, comportement d'Echoflex)
    const float r = b.getWidth() * (layout::footR / layout::fsS) * 0.95f;
    const auto c = b.getCentre().translated (b.getWidth() * 0.002f, b.getWidth() * 0.004f);
    ColourGradient shade (Colours::black.withAlpha (0.25f), c.x, c.y, Colours::black.withAlpha (0.0f), c.x + r, c.y, true);
    shade.addColour (0.8, Colours::black.withAlpha (0.22f));
    g.setGradientFill (shade);
    g.fillEllipse (c.x - r, c.y - r, r * 2.0f, r * 2.0f);
}

void FootSwitchArea::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { if (onRightClick) onRightClick(); return; }
    pressed = true;
    repaint();
    const bool momentary = mom != nullptr && mom->load() > 0.5f;
    attachment.setValueAsCompleteGesture (momentary ? 1.0f : (value ? 0.0f : 1.0f));   // bascule des l'appui
    if (onUserChange) onUserChange();
}

void FootSwitchArea::mouseUp (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) return;
    const bool momentary = mom != nullptr && mom->load() > 0.5f;
    if (pressed && momentary)                       // MOMENTARY ON : le larsen s'arrete au relachement
    {
        attachment.setValueAsCompleteGesture (0.0f);
        if (onUserChange) onUserChange();
    }
    pressed = false;
    repaint();
}

//==============================================================================
// EDITEUR
//==============================================================================
FreakoutAudioProcessorEditor::FreakoutAudioProcessorEditor (FreakoutAudioProcessor& p)
    : AudioProcessorEditor (&p), proc (p),
      range (*p.apvts.getParameter ("gain"), *p.apvts.getParameter ("onset")),
      typeKnob (*p.apvts.getParameter ("type")),
      momentarySw (*p.apvts.getParameter ("momentary")),
      drySw (*p.apvts.getParameter ("dry")),
      foot (*p.apvts.getParameter ("active"), p.apvts.getRawParameterValue ("momentary"))
{
    setLookAndFeel (&lnf);                 // menus au design d'Octopus (+ poignee de redimensionnement)
    background = ImageCache::getFromMemory (BinaryData::background_png, BinaryData::background_pngSize);
    glowStrip  = ImageCache::getFromMemory (BinaryData::glow_strip_png, BinaryData::glow_strip_pngSize);
    ledOn      = ImageCache::getFromMemory (BinaryData::led_on_png, BinaryData::led_on_pngSize);
    const auto strip = ImageCache::getFromMemory (BinaryData::toggle_strip_png, BinaryData::toggle_strip_pngSize);
    foot.down  = ImageCache::getFromMemory (BinaryData::fs_down_png, BinaryData::fs_down_pngSize);
    // Poppins (serigraphie, ecran, menus) et logo NINE HANDS | DSP vectoriel
    regFace   = Typeface::createSystemTypefaceFor (BinaryData::PoppinsRegular_ttf, BinaryData::PoppinsRegular_ttfSize);
    labelFace = Typeface::createSystemTypefaceFor (BinaryData::PoppinsMedium_ttf, BinaryData::PoppinsMedium_ttfSize);
    boldFace  = Typeface::createSystemTypefaceFor (BinaryData::PoppinsBold_ttf, BinaryData::PoppinsBold_ttfSize);
    lightFace = Typeface::createSystemTypefaceFor (BinaryData::PoppinsLight_ttf, BinaryData::PoppinsLight_ttfSize);
    lnf.f = { regFace, labelFace, boldFace };
    glowPc = NineHandsGlow::percent (JucePlugin_Name);
    if (auto xml = XmlDocument::parse (String::fromUTF8 (BinaryData::NineHandsLogo_svg, BinaryData::NineHandsLogo_svgSize)))
        logo = Drawable::createFromSVG (*xml);
    buildPrint();

    auto edited = [this] { proc.currentPreset = -1; };
    // index des commandes = learnDef du processeur (0 Gain, 1 Onset, 2 Type, 3 Momentary, 4 Dry, 5 footswitch)
    range.onRightClick = [this] { showContextMenu (range.rightZone == 1 ? 1 : 0); };
    range.onUserChange = edited;
    range.onTouched = [this] (int which) { lastChanged = which; showStatus(); };
    range.onValue = [this] { askRepaint (range.getBounds()); };
    typeKnob.onRightClick = [this] { showContextMenu (2); };
    typeKnob.onUserChange = edited;
    for (auto* l : { &momentarySw, &drySw })
    {
        l->strip = strip;
        l->onUserChange = edited;
    }
    momentarySw.onRightClick = [this] { showContextMenu (3); };
    drySw.onRightClick       = [this] { showContextMenu (4); };
    foot.onRightClick = [this] { showContextMenu (5); };
    addAndMakeVisible (range);
    addAndMakeVisible (typeKnob);
    addAndMakeVisible (momentarySw);
    addAndMakeVisible (drySw);
    addAndMakeVisible (foot);

    for (int i = 0; i < numValueIds; ++i) lastValues[i] = proc.raw (valueIds[i]);
    lastPresetCounter = proc.presetCounter.load();
    lastMidiCount = proc.midiCounter.load();
    ledLevel = proc.raw ("active") > 0.5f ? 1.0f : 0.0f;

    // taille par defaut = taille minimale (impossible de reduire en dessous), proportions bloquees
    const int defaultW = roundToInt ((float) defaultH * baseW / baseH);
    setResizable (true, true);
    setResizeLimits (defaultW, defaultH, roundToInt ((float) maxH * baseW / baseH), maxH);
    hostLock.setLimits (defaultW, defaultH, roundToInt ((float) maxH * baseW / baseH), maxH);
    if (auto* cons = getConstrainer())
        cons->setFixedAspectRatio ((double) baseW / (double) baseH);
    setOpaque (true);
    setSize (defaultW, defaultH);
    // taille des nouvelles fenetres : celle choisie dans le menu « Default size (new windows) »
    setScaledHeight (sizeHeight (NineHandsWindow::openIndex (JucePlugin_Name, proc.uiSizeIdx.load(), numSizes)));   // taille du projet, sinon taille par defaut
    rebuildCaches();
    startTimerHz (30);
}

FreakoutAudioProcessorEditor::~FreakoutAudioProcessorEditor() { stopTimer(); setLookAndFeel (nullptr); }


//==============================================================================
int FreakoutAudioProcessorEditor::sizeHeight (int idx)
{
    const int h[numSizes] = { (int) defaultH, roundToInt (refH * 0.75f), (int) refH };
    return h[jlimit (0, numSizes - 1, idx)];
}

void FreakoutAudioProcessorEditor::setScaledHeight (int h)
{
    h = jlimit ((int) defaultH, (int) maxH, h);
    setSize (roundToInt ((float) h * baseW / baseH), h);
    hostLock.enforce();
}

Rectangle<int> FreakoutAudioProcessorEditor::scaled (Rectangle<float> r) const
{
    const float s = (float) getHeight() / baseH;
    return r.transformedBy (AffineTransform::scale (s)).getSmallestIntegerContainer();
}

float FreakoutAudioProcessorEditor::physicalScale() const
{
    if (forcedScale > 0.0f) return forcedScale;
    return jlimit (1.0f, 4.0f, (float) Component::getApproximateScaleFactorForComponent (this));
}

void FreakoutAudioProcessorEditor::showStatus() { statusUntil = Time::getMillisecondCounterHiRes() + 2500.0; }

//==============================================================================
// caches d'affichage : fond et calques lumineux a la taille de la fenetre (reconstruits par le timer seulement)
//==============================================================================
void FreakoutAudioProcessorEditor::rebuildCaches (float sc)
{
    if (sc <= 0.0f) sc = cacheScale > 0.0f ? cacheScale : physicalScale();
    const int w = getWidth(), h = getHeight();
    if (w <= 0 || h <= 0) return;
    if (w == cacheW && h == cacheH && std::abs (sc - cacheScale) < 0.01f && bgScaled.isValid()) return;
    cacheW = w; cacheH = h; cacheScale = sc;

    // fond a la resolution physique de l'ecran (net sur Retina / 4K) ; jamais agrandi au-dela de l'image d'origine
    const int pw = roundToInt ((float) w * sc), ph = roundToInt ((float) h * sc);
    bgScaled = (pw >= background.getWidth()) ? background : background.rescaled (pw, ph, Graphics::highResamplingQuality);

    const float s = (float) h / baseH;
    const auto gr = layout::glowRect;
    const int lw = glowStrip.getWidth(), lh = glowStrip.getHeight() / 5;
    const int tw = roundToInt (gr.getWidth() * s * sc), th = roundToInt (gr.getHeight() * s * sc);
    for (int k = 0; k < 5; ++k)
    {
        auto layer = glowStrip.getClippedImage ({ 0, k * lh, lw, lh });
        glowScaled[k] = (tw >= lw) ? layer.createCopy() : layer.rescaled (tw, th, Graphics::highResamplingQuality);
    }
    const int lp = roundToInt (layout::ledS * s * sc);
    ledOnS = (lp >= ledOn.getWidth()) ? ledOn : ledOn.rescaled (lp, lp, Graphics::highResamplingQuality);
    repaint();
}

void FreakoutAudioProcessorEditor::resized()
{
    // anti-gel : jamais de setSize ici ; les limites du constrainer suffisent
    auto sq = [] (Point<float> c, float half) { return Rectangle<float> (c.x - half, c.y - half, half * 2.0f, half * 2.0f); };
    range.setBounds (scaled (sq (layout::rangePos, layout::skirtR)));
    typeKnob.setBounds (scaled (sq (layout::typePos, layout::typeR)));
    momentarySw.setBounds (scaled (sq (layout::momentaryPos, layout::togS * 0.5f)));
    drySw.setBounds (scaled (sq (layout::dryPos, layout::togS * 0.5f)));
    foot.setBounds (scaled (sq (layout::fsPos, layout::fsS * 0.5f)));
    resizeSettle = 4;
}

//==============================================================================
// Anti-gel v2 (NINE HANDS | DSP) :
//  1. moteur de rendu logiciel force sur Windows, applique a chaque nouvelle fenetre hote et reverifie toutes les secondes ;
//  2. aucun calcul lourd dans paint() : caches reconstruits par le timer (apres stabilisation de la taille / changement d'echelle) ;
//  3. chien de garde : redessin demande non servi depuis 1,5 s -> moteur de rendu reapplique, fenetre redessinee ;
//  4. cote audio : aucun appel a l'hote ni allocation depuis le thread audio (voir PluginProcessor).
void FreakoutAudioProcessorEditor::useSoftwareRenderer()
{
    auto* peer = getPeer();
    if (peer != lastPeer) { lastPeer = peer; repaint(); }
   #if JUCE_WINDOWS
    if (peer != nullptr)
    {
        int sw = peer->getAvailableRenderingEngines().indexOf ("Software Renderer");
        if (sw < 0) sw = 0;
        if (peer->getCurrentRenderingEngine() != sw)
            peer->setCurrentRenderingEngine (sw);
    }
   #endif
}

void FreakoutAudioProcessorEditor::parentHierarchyChanged() { useSoftwareRenderer(); hostLock.track (*this); }
void FreakoutAudioProcessorEditor::visibilityChanged()      { useSoftwareRenderer(); if (isShowing()) repaint(); }

void FreakoutAudioProcessorEditor::askRepaint (Rectangle<int> r)
{
    if (repaintAskedMs <= 0.0) repaintAskedMs = Time::getMillisecondCounterHiRes();
    repaint (r);
}

//==============================================================================
static String noteName (float hz)
{
    if (hz <= 0.0f) return {};
    static const char* n[12] = { "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" };
    const int midi = roundToInt (69.0f + 12.0f * std::log2 (hz / 440.0f));
    return String (n[((midi % 12) + 12) % 12]) + String (midi / 12 - 1);
}

String FreakoutAudioProcessorEditor::buildStatusLine() const
{
    const int i = lastChanged;
    if (i < 0) return {};
    const float v = proc.raw (valueIds[i]);
    switch (i)
    {
        case 0: return "GAIN  " + String (roundToInt (v * 10.0f)) + " %";
        case 1: return "ONSET  " + String (roundToInt (v * 10.0f)) + " %";
        case 2: return "TYPE  " + FreakoutAudioProcessor::typeNames()[jlimit (0, 6, roundToInt (v))];
        case 3: return v > 0.5f ? "MOMENTARY  ON" : "MOMENTARY  OFF";
        case 4: return v > 0.5f ? "DRY  ON" : "DRY  OFF";
        case 5: return v > 0.5f ? "EFFECT  ON" : "BYPASS";
        default: return "SENSITIVITY  " + FreakoutAudioProcessor::sensNames()[jlimit (0, 2, roundToInt (v))].toUpperCase();
    }
}

// au repos : ce qui larsene en ce moment (harmonique, frequence, note)
String FreakoutAudioProcessorEditor::buildInfoLine() const
{
    const auto type = FreakoutAudioProcessor::typeNames()[jlimit (0, 6, roundToInt (proc.raw ("type")))];
    if (proc.raw ("active") < 0.5f) return proc.raw ("momentary") > 0.5f ? "HOLD THE FOOTSWITCH" : "BYPASS";
    const float hz = proc.fbHz.load();
    if (proc.meter.load() < 0.03f || hz <= 0.0f) return "TYPE  " + type;
    const int h = proc.fbHarmonic.load();
    const String hs = h < 0 ? String ("SUB") : ("H" + String (h));
    return hs + "   " + String (roundToInt (hz)) + " Hz   " + noteName (hz);
}

String FreakoutAudioProcessorEditor::buildPresetLine() const
{
    const int cp = proc.currentPreset.load();
    String s;
    if (cp >= 0 && cp < FreakoutAudioProcessor::getNumFactoryPresets())
        s << "P" << (cp + 1) << "  " << FreakoutAudioProcessor::getFactoryPreset (cp).name;
    else if (cp > 100) s << "User " << (cp - 100);
    else               s << "Edited";
    return s;
}

//==============================================================================
void FreakoutAudioProcessorEditor::timerCallback()
{
    const double now = Time::getMillisecondCounterHiRes();
    if (getPeer() != lastPeer || now - lastRendererCheckMs > 1000.0) { lastRendererCheckMs = now; useSoftwareRenderer(); }
    if (now - lastGlowReadMs > 3000.0)       // clic droit > Glow intensity : commun a toutes les fenetres (jamais dans paint)
    {
        lastGlowReadMs = now;
        const int pc = NineHandsGlow::percent (JucePlugin_Name);
        if (pc != glowPc) setGlowPercent (pc);
    }
    hostLock.track (*this);

    if (resizeSettle > 0 && --resizeSettle == 0) rebuildCaches();
    else if (resizeSettle == 0 && now - lastScaleCheckMs > 250.0)
    {
        lastScaleCheckMs = now;
        const float sc = physicalScale();
        if (std::abs (sc - cacheScale) > 0.01f) rebuildCaches (sc);
    }

    if (repaintAskedMs > 0.0 && isShowing() && now - repaintAskedMs > 1500.0 && lastPaintMs < repaintAskedMs)
    {
        repaintAskedMs = 0.0;
        lastPeer = nullptr;
        useSoftwareRenderer();
        repaint();
    }

    momentarySw.tick (now);
    drySw.tick (now);
    if (typeKnob.tick()) askRepaint (typeKnob.getBounds());

    // ligne d'etat : apparait quand un reglage bouge, reste 2,5 s puis s'efface
    int changed = -1, numChanged = 0;
    for (int i = 0; i < numValueIds; ++i)
    {
        const float v = proc.raw (valueIds[i]);
        if (std::abs (v - lastValues[i]) > 1.0e-4f) { lastValues[i] = v; changed = i; ++numChanged; }
    }
    const int pcount = proc.presetCounter.load();
    if (pcount != lastPresetCounter) { lastPresetCounter = pcount; numChanged = 0; }
    if (numChanged == 1 && changed != 5) { lastChanged = changed; showStatus(); learnLineUntil = 0.0; }
    if (range.dragging >= 0) { lastChanged = range.dragging; showStatus(); learnLineUntil = 0.0; }
    // MIDI Learn : attente puis confirmation 2 s dans l'afficheur
    const int lt = proc.learnTarget.load();
    const int learned = proc.lastLearned.exchange (-1);
    if (learned >= 0)
    {
        learnLine = String (FreakoutAudioProcessor::learnDef (learned).name) + " = CC " + String (proc.ccMap[learned].load());
        learnLineUntil = now + 2000.0;
        statusUntil = jmax (statusUntil, learnLineUntil);
    }
    else if (lt >= 0)
    {
        learnLine = "MIDI LEARN: move a control for " + String (FreakoutAudioProcessor::learnDef (lt).name);
        learnLineUntil = now + 200.0;
        statusUntil = jmax (statusUntil, now + 200.0);
    }
    const int mc = proc.midiCounter.load();
    if (mc != lastMidiCount) { lastMidiCount = mc; midiFlash = 8; }
    if (midiFlash > 0) --midiFlash;

    const float target = now < statusUntil ? 1.0f : 0.0f;
    statusAlpha += (target - statusAlpha) * (target > statusAlpha ? 0.45f : 0.12f);
    if (statusAlpha < 0.005f) statusAlpha = 0.0f;
    if (statusAlpha > 0.995f) statusAlpha = 1.0f;

    // echelle de LED : LED centrale = effet actif, puis paires de l'interieur vers l'exterieur selon la montee du larsen
    const bool on = proc.raw ("active") > 0.5f;
    ledLevel += ((on ? 1.0f : 0.0f) - ledLevel) * (on ? 0.45f : 0.28f);
    if (ledLevel < 0.003f) ledLevel = 0.0f;
    if (ledLevel > 0.997f) ledLevel = 1.0f;
    const float m = on ? proc.meter.load() : 0.0f;
    meterShown += (m - meterShown) * (m > meterShown ? 0.5f : 0.25f);
    if (std::abs (meterShown - m) < 0.002f) meterShown = m;

    bool ledsChanged = false;
    for (int i = 0; i < 9; ++i)
    {
        const int pair = std::abs (i - 4);
        const float b = pair == 0 ? ledLevel : ledLevel * jlimit (0.0f, 1.0f, meterShown * 4.0f - (float) (pair - 1));
        ledB[i] = b;
        if (std::abs (b - drawnLedB[i]) > 0.004f) { drawnLedB[i] = b; ledsChanged = true; }
    }
    const float glowKey = ledLevel * 10.0f + meterShown;
    if (ledsChanged || std::abs (glowKey - drawnGlow) > 0.004f)
    {
        drawnGlow = glowKey;
        askRepaint (scaled (layout::glowRect));
    }

    // (le message de learn reste pendant le fondu de sortie)
    const auto l1 = (learnLineUntil > 0.0 && now < learnLineUntil + 800.0 ? learnLine : buildStatusLine()), info = buildInfoLine(), pl = buildPresetLine();
    const bool textChanged = l1 != lastLine1 || info != lastInfo;
    lastLine1 = l1; lastInfo = info;
    if (std::abs (statusAlpha - drawnStatus) > 0.003f || textChanged)
    {
        drawnStatus = statusAlpha;
        askRepaint (scaled (statusRect.expanded (4.0f)));
    }
    if (pl != lastPreset || hoverZone != drawnHover || midiFlash > 0)
    {
        lastPreset = pl; drawnHover = hoverZone;
        askRepaint (scaled (presetRect.expanded (3.0f)));
    }
}

//==============================================================================
// Serigraphie vectorielle : construite une fois en chemins (unites du plugin), remplie a l'echelle de la fenetre :
// textes Poppins, graduations, filets, fleches, pictogrammes, cadre grave, onde du titre, couronne du footswitch.
//==============================================================================
void FreakoutAudioProcessorEditor::buildPrint()
{
    printDark.clear(); printLight.clear(); framePath.clear(); wavePath.clear();
    for (const auto& t : layout::texts)
    {
        const Typeface::Ptr face = t.font == 1 ? boldFace : (t.font == 2 ? lightFace : (t.font == 3 ? regFace : labelFace));
        const Font font (FontOptions (face).withPointHeight (t.em));
        const String str (t.s);
        float total = 0.0f;
        for (int i = 0; i < str.length(); ++i)
            total += GlyphArrangement::getStringWidth (font, String::charToString (str[i])) + (i > 0 ? t.track : 0.0f);
        const float base = (font.getAscent() - font.getDescent()) * 0.5f;     // centre vertical entre ascendante et descendante
        GlyphArrangement ga;
        float x = -total * 0.5f;
        for (int i = 0; i < str.length(); ++i)
        {
            const String ch = String::charToString (str[i]);
            ga.addLineOfText (font, ch, x, base);
            x += GlyphArrangement::getStringWidth (font, ch) + t.track;
        }
        Path p; ga.createPath (p);
        if (t.rot == 0.0f && ! p.isEmpty())        // centrage sur l'encre (et non sur les chasses) : titre et sous-titre au milieu exact
            p.applyTransform (AffineTransform::translation (-p.getBounds().getCentreX(), 0.0f));
        p.applyTransform (AffineTransform::rotation (-t.rot * MathConstants<float>::pi / 180.0f).translated (t.x, t.y));
        (t.ink == 1 ? printLight : printDark).addPath (p);
    }
    for (const auto& l : layout::lines)
    {
        Path seg; seg.startNewSubPath (l.x0, l.y0); seg.lineTo (l.x1, l.y1);
        Path st; PathStrokeType (l.w, PathStrokeType::mitered, PathStrokeType::butt).createStrokedPath (st, seg);
        (l.ink == 1 ? printLight : printDark).addPath (st);
    }
    for (const auto& t : layout::tris)
    {
        Path p; p.addTriangle (t.x0, t.y0, t.x1, t.y1, t.x2, t.y2);
        (t.ink == 1 ? printLight : printDark).addPath (p);
    }
    for (const auto& ic : layout::icons)
    {
        Path ring; ring.addEllipse (ic.x - 5.5f, ic.y - 5.5f, 11.0f, 11.0f);
        Path st; PathStrokeType (1.4f).createStrokedPath (st, ring);
        printDark.addPath (st);
        if (ic.inner) printDark.addEllipse (ic.x - 2.4f, ic.y - 2.4f, 4.8f, 4.8f);
    }
    // couronne du footswitch
    {
        Path ring; ring.addEllipse (layout::fsPos.x - layout::fsRing, layout::fsPos.y - layout::fsRing, layout::fsRing * 2.0f, layout::fsRing * 2.0f);
        Path st; PathStrokeType (1.8f).createStrokedPath (st, ring);
        printDark.addPath (st);
    }
    // onde de larsen du titre (traits arrondis)
    for (const auto& w : layout::wave)
    {
        Path seg; seg.startNewSubPath (w.p[0], w.p[1]);
        for (int i = 1; i < w.n; ++i) seg.lineTo (w.p[2 * i], w.p[2 * i + 1]);
        Path st; PathStrokeType (layout::waveW, PathStrokeType::curved, PathStrokeType::rounded).createStrokedPath (st, seg);
        wavePath.addPath (st);
    }
    // cadre grave du boitier
    framePath.addRoundedRectangle (layout::frame[0], layout::frame[1], layout::frame[2], layout::frame[3], layout::frame[4]);
}

void FreakoutAudioProcessorEditor::drawPrint (Graphics& g)
{
    // cadre grave : rainure sombre, arete claire du cote eclaire (bas / droite de la rainure), lumiere en haut a gauche
    g.setColour (Colours::white.withAlpha (0.55f));
    g.strokePath (framePath, PathStrokeType (1.1f), AffineTransform::translation (0.75f, 0.95f));
    g.setColour (Colour (0xff2a2b2f).withAlpha (0.92f));
    g.strokePath (framePath, PathStrokeType (1.5f));
    g.setColour (inkDark);
    g.fillPath (printDark);
    g.fillPath (wavePath);
    g.setColour (inkLight);
    g.fillPath (printLight);
    if (logo != nullptr)
    {
        const auto vb = logo->getDrawableBounds();
        const float w = layout::logoW, h = w * vb.getHeight() / jmax (1.0f, vb.getWidth());
        logo->drawWithin (g, { layout::logoPos.x - w * 0.5f, layout::logoPos.y - h * 0.5f, w, h }, RectanglePlacement::centred, 0.92f);
    }
}

void FreakoutAudioProcessorEditor::drawLeds (Graphics& g)
{
    if (ledLevel <= 0.003f) return;
    // la facade recoit la lumiere des LED : calques precalcules (fond x eclairement x couleur), 5 etats cumulatifs
    const float s4 = jlimit (0.0f, 4.0f, meterShown * 4.0f);
    const int k = jmin (3, (int) s4);
    const float frac = s4 - (float) k;
    if (glowScaled[0].isValid())
    {
        g.setOpacity (ledLevel * glowAmt());                            // halo : clic droit > Glow intensity
        g.drawImage (glowScaled[k], layout::glowRect);
        if (frac > 0.003f || s4 >= 4.0f)
        {
            g.setOpacity (ledLevel * (s4 >= 4.0f ? 1.0f : frac) * glowAmt());
            g.drawImage (glowScaled[s4 >= 4.0f ? 4 : k + 1], layout::glowRect);
        }
    }
    // lentilles allumees (photo de LED), chacune a son intensite
    const Image& lo = ledOnS.isValid() ? ledOnS : ledOn;
    const float hs = layout::ledS * 0.5f;
    for (int i = 0; i < 9; ++i)
    {
        if (ledB[i] <= 0.003f || ! lo.isValid()) continue;
        const auto c = layout::ledPos[i];
        g.setOpacity (ledB[i]);
        g.drawImage (lo, { c.x - hs, c.y - hs, hs * 2.0f, hs * 2.0f });
    }
    g.setOpacity (1.0f);
}

void FreakoutAudioProcessorEditor::drawDisplay (Graphics& g)
{
    // ligne du haut : reglage qui vient de bouger (fondu), sinon ce qui larsene en ce moment ; ambre sur verre fume
    const float a = statusAlpha;
    const auto sr = statusRect.toNearestInt();
    auto glowText = [&] (const String& t, Font f, float alpha)
    {
        g.setFont (f);
        g.setColour (lcd.withAlpha (0.14f * alpha));                    // leger halo de l'afficheur
        for (auto d : { Point<float> (-0.8f, 0.0f), Point<float> (0.8f, 0.0f), Point<float> (0.0f, -0.8f), Point<float> (0.0f, 0.8f) })
            g.drawFittedText (t, sr.toFloat().translated (d.x, d.y).toNearestInt(), Justification::centred, 1, 0.8f);
        g.setColour (lcd.withAlpha (alpha));
        g.drawFittedText (t, sr, Justification::centred, 1, 0.8f);
    };
    const Font big (FontOptions (labelFace).withHeight (25.0f));
    if (a < 0.999f) glowText (lastInfo, big.withExtraKerningFactor (0.04f), 0.95f * (1.0f - a));
    if (a > 0.0f)   glowText (lastLine1, (lastLine1.length() > 24 ? big.withHeight (18.0f) : big).withExtraKerningFactor (0.04f), a);

    // barre de presets : cadre fin, fleches et nom
    const auto r = presetRect;
    g.setColour (presetInk.withAlpha (hoverZone != 0 ? 0.45f : 0.20f));
    g.drawRoundedRectangle (r.reduced (0.6f), r.getHeight() * 0.5f, 1.1f);
    if (hoverZone != 0)
    {
        g.setColour (Colours::white.withAlpha (0.04f));
        g.fillRoundedRectangle (r.reduced (1.2f), r.getHeight() * 0.5f);
    }
    const float aw = 32.0f;
    auto arrow = [&] (Rectangle<float> ar, bool left, bool hot)
    {
        Path p;
        const auto c = ar.getCentre();
        const float sz = 4.8f;
        if (left) p.addTriangle (c.x + sz * 0.6f, c.y - sz, c.x + sz * 0.6f, c.y + sz, c.x - sz * 0.8f, c.y);
        else      p.addTriangle (c.x - sz * 0.6f, c.y - sz, c.x - sz * 0.6f, c.y + sz, c.x + sz * 0.8f, c.y);
        g.setColour (presetInk.withAlpha (hot ? 1.0f : 0.7f));
        g.fillPath (p);
    };
    arrow (r.withWidth (aw), true, hoverZone == 1);
    arrow (r.withTrimmedLeft (r.getWidth() - aw), false, hoverZone == 3);
    g.setFont (Font (FontOptions (labelFace).withHeight (17.0f)).withExtraKerningFactor (0.02f));
    g.setColour ((midiFlash > 0 ? Colour (0xffffb08a) : presetInk).withAlpha (hoverZone == 2 ? 1.0f : 0.9f));
    g.drawFittedText (lastPreset, r.reduced (aw, 0.0f).toNearestInt(), Justification::centred, 1, 0.75f);
}

void FreakoutAudioProcessorEditor::drawKnobs (Graphics& g)
{
    // reperes creme (comme sur la photo du potard) : seuls les reperes tournent, reflets et moletage restent fixes
    paintPointer (g, layout::rangePos, layout::skirtR, knobAngle (range.valueOf (1)), 0.70f, 0.93f, 4.4f);   // ONSET (jupe)
    paintPointer (g, layout::rangePos, layout::capR, knobAngle (range.valueOf (0)), 0.28f, 0.90f, 2.9f);     // GAIN (chapeau)
    paintPointer (g, layout::typePos, layout::typeR, typeKnob.getShownAngle(), 0.28f, 0.90f, 3.2f);         // TYPE
}

void FreakoutAudioProcessorEditor::paint (Graphics& g)
{
    lastPaintMs = Time::getMillisecondCounterHiRes();
    repaintAskedMs = 0.0;
    g.fillAll (Colour (0xff111112));          // autour des jacks : le fond de l'image est transparent
    // anti-gel : aucun rescale ici, on dessine le cache existant (ou l'original en attendant le timer)
    const Image& bg = bgScaled.isValid() ? bgScaled : background;
    g.setImageResamplingQuality (&bg == &background ? Graphics::highResamplingQuality : Graphics::lowResamplingQuality);
    if (bg.isValid()) g.drawImage (bg, getLocalBounds().toFloat());

    const float s = (float) getHeight() / baseH;
    g.addTransform (AffineTransform::scale (s));
    g.setImageResamplingQuality (Graphics::mediumResamplingQuality);
    drawLeds (g);
    drawPrint (g);
    drawKnobs (g);
    drawDisplay (g);
}

void FreakoutAudioProcessorEditor::pressFootswitchForCapture (bool down)
{
    const Point<float> c = foot.getLocalBounds().getCentre().toFloat();
    auto src = Desktop::getInstance().getMainMouseSource();
    const MouseEvent ev (src, c, ModifierKeys (ModifierKeys::leftButtonModifier), 1.0f, 0, 0, 0, 0, &foot, &foot,
                         Time::getCurrentTime(), c, Time::getCurrentTime(), 1, false);
    if (down) foot.mouseDown (ev); else foot.mouseUp (ev);
}

//==============================================================================
// souris : barre de presets (fleches = precedent / suivant, nom = menu), clic droit = menu
//==============================================================================
static int presetZoneAt (Point<float> p)
{
    if (! presetRect.contains (p)) return 0;
    if (p.x < presetRect.getX() + 32.0f) return 1;
    if (p.x > presetRect.getRight() - 32.0f) return 3;
    return 2;
}

void FreakoutAudioProcessorEditor::mouseMove (const MouseEvent& e)
{
    const float s = (float) getHeight() / baseH;
    hoverZone = presetZoneAt (e.position / s);
    setMouseCursor (hoverZone != 0 ? MouseCursor::PointingHandCursor : MouseCursor::NormalCursor);
}

void FreakoutAudioProcessorEditor::mouseExit (const MouseEvent&) { hoverZone = 0; }

void FreakoutAudioProcessorEditor::mouseDown (const MouseEvent& e)
{
    if (e.mods.isPopupMenu()) { showContextMenu(); return; }
    const float s = (float) getHeight() / baseH;
    switch (presetZoneAt (e.position / s))
    {
        case 1: stepPreset (-1); break;
        case 2: showPresetMenu(); break;
        case 3: stepPreset (1); break;
        default: break;
    }
}

void FreakoutAudioProcessorEditor::stepPreset (int delta)
{
    const int n = FreakoutAudioProcessor::getNumFactoryPresets();
    int cp = proc.currentPreset.load();
    if (cp < 0 || cp >= n) cp = delta > 0 ? -1 : 0;
    proc.applyFactoryPreset ((cp + delta + n) % n);
}

void FreakoutAudioProcessorEditor::showPresetMenu()
{
    PopupMenu m;
    m.addSectionHeader ("Factory presets");
    for (int i = 0; i < FreakoutAudioProcessor::getNumFactoryPresets(); ++i)
        m.addItem (100 + i, String (i + 1) + ". " + FreakoutAudioProcessor::getFactoryPreset (i).name, true, proc.currentPreset.load() == i);
    m.addSeparator();
    PopupMenu load, save;
    for (int slot = 1; slot <= 9; ++slot)
    {
        const bool exists = proc.hasUserPreset (slot);
        load.addItem (200 + slot, "User " + String (slot) + (exists ? "" : "  (empty)"), exists, proc.currentPreset.load() == 100 + slot);
        save.addItem (300 + slot, "User " + String (slot) + (exists ? "  (overwrite)" : ""));
    }
    m.addSubMenu ("Load user preset", load);
    m.addSubMenu ("Save user preset", save);
    m.setLookAndFeel (&lnf);
    m.showMenuAsync (PopupMenu::Options().withTargetScreenArea (localAreaToGlobal (scaled (presetRect))),
        [safe = Component::SafePointer<FreakoutAudioProcessorEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& pr = safe->proc;
            if      (r >= 100 && r < 200) pr.applyFactoryPreset (r - 100);
            else if (r > 200 && r < 300)  pr.loadUserPreset (r - 200);
            else if (r > 300 && r < 400)  pr.saveUserPreset (r - 300);
        });
}


void FreakoutAudioProcessorEditor::handleMidiMenu (int r)
{
    if (r >= 1000 && r < 1000 + FreakoutAudioProcessor::numLearn)
        proc.learnTarget.store (proc.learnTarget.load() == r - 1000 ? -1 : r - 1000);   // re-cliquer annule
    else if (r >= 1100 && r < 1100 + FreakoutAudioProcessor::numLearn) proc.ccMap[r - 1100].store (-1);
    else if (r == 1200) proc.learnTarget.store (-1);
    else if (r == 1201) { proc.learnTarget.store (-1); proc.clearMidiMap(); }
}

void FreakoutAudioProcessorEditor::setGlowPercent (int pc)
{
    glowPc = NineHandsGlow::sanitize (pc);
    drawnGlow = -1.0f;                      // le timer redessine la lumiere des LED
}

PopupMenu FreakoutAudioProcessorEditor::buildContextMenu (int learnIdx)
{
    using namespace NineHandsMenu;
    PopupMenu menu;
    menu.setLookAndFeel (&lnf);
    auto ccText = [this] (int i)
    {
        const int cc = proc.ccMap[i].load();
        return cc >= 0 ? "CC " + String (cc) : String ("not assigned");
    };
    const int lt = proc.learnTarget.load();
    if (learnIdx >= 0)
    {
        // menu d'une commande (tronc commun) : en-tete, MIDI Learn, Clear MIDI, Cancel MIDI learn
        const int i = learnIdx;
        const String name = FreakoutAudioProcessor::learnDef (i).name;
        addHeader (menu, lnf.f, (learnIdx < 2 ? icoKnob : (learnIdx < 5 ? icoSwitch : icoPedal)), lcd, name, "MIDI: " + ccText (learnIdx));
        menu.addItem (1000 + learnIdx, "MIDI Learn: " + name, true, lt == learnIdx);
        menu.addItem (1100 + learnIdx, "Clear MIDI: " + name, proc.ccMap[learnIdx].load() >= 0);
        menu.addItem (1200, "Cancel MIDI learn", lt >= 0);
        return menu;
    }

    // menu de la pedale (tronc commun) : presets, reglages propres, MIDI, Plugin size, Glow intensity
    addHeader (menu, lnf.f, icoPedal, lcd, "FreakOut", "Feedback  v" + String (JucePlugin_VersionString));
    PopupMenu factory;
    for (int i = 0; i < FreakoutAudioProcessor::getNumFactoryPresets(); ++i)
        factory.addItem (100 + i, String (i + 1) + ". " + FreakoutAudioProcessor::getFactoryPreset (i).name, true, proc.currentPreset.load() == i);
    menu.addSubMenu ("Factory presets", factory);
    PopupMenu load, save;
    for (int slot = 1; slot <= 9; ++slot)
    {{
        const bool exists = proc.hasUserPreset (slot);
        load.addItem (200 + slot, "User " + String (slot) + (exists ? "" : "  (empty)"), exists, proc.currentPreset.load() == 100 + slot);
        save.addItem (300 + slot, "User " + String (slot) + (exists ? "  (overwrite)" : ""));
    }}
    menu.addSubMenu ("Load user preset", load);
    menu.addSubMenu ("Save user preset", save);
    menu.addSeparator();
    PopupMenu sens;
    const int sNow = jlimit (0, 2, roundToInt (proc.raw ("sensitivity")));
    const char* sensHelp[3] = { "Low (hot pickups, noisy room)", "Normal (default)", "High (low output, clean playing)" };
    for (int i = 0; i < 3; ++i) sens.addItem (50 + i, sensHelp[i], true, sNow == i);
    menu.addSubMenu ("Trigger sensitivity", sens);
    menu.addSeparator();

    PopupMenu midi;
    midi.addSectionHeader ("MIDI Learn");
    for (int i = 0; i < FreakoutAudioProcessor::numLearn; ++i)
        midi.addItem (1000 + i, "Learn: " + String (FreakoutAudioProcessor::learnDef (i).name) + "  (" + ccText (i) + ")", true, lt == i);
    midi.addSeparator();
    midi.addItem (1200, "Cancel MIDI learn", lt >= 0);
    midi.addItem (1201, "Clear all MIDI assignments");
    midi.addSeparator();
    NineHandsWindow::addMidiFootswitchMode (midi, proc.raw ("midiFsMode") < 0.5f);
    midi.addSeparator();
    NineHandsWindow::addProgramChangeInfo (midi);
    menu.addSubMenu ("MIDI", midi);
    menu.addSeparator();

    const char* names[numSizes] = { "60 %", "75 %", "100 %" };
    const int heights[numSizes] = { sizeHeight (0), sizeHeight (1), sizeHeight (2) };
    menu.addSubMenu ("Plugin size", NineHandsWindow::sizeMenu (JucePlugin_Name, numSizes, names, heights, getHeight()));
    menu.addSubMenu ("Glow intensity", NineHandsWindow::glowMenu (glowPc));
    return menu;
}

void FreakoutAudioProcessorEditor::showContextMenu (int learnIdx)
{
    auto menu = buildContextMenu (learnIdx);
    menu.showMenuAsync (PopupMenu::Options().withMousePosition(),       // menu clic droit : toujours la ou l'on clique
        [safe = Component::SafePointer<FreakoutAudioProcessorEditor> (this)] (int r)
        {
            if (safe == nullptr || r == 0) return;
            auto& ed = *safe;
            auto& pr = ed.proc;
            int inst = pr.uiSizeIdx.load();
            const int sz = NineHandsWindow::handleSize (r, JucePlugin_Name, numSizes, inst);
            if (sz >= 0) { pr.uiSizeIdx = inst; ed.setScaledHeight (ed.sizeHeight (sz)); return; }
            if (const int pc = NineHandsWindow::handleGlow (r, JucePlugin_Name))
            {
                ed.setGlowPercent (pc);
                ed.learnLine = "Glow  " + String (pc) + " %";        // ligne d'etat, brievement
                ed.learnLineUntil = Time::getMillisecondCounterHiRes() + 1500.0;
                ed.statusUntil = jmax (ed.statusUntil, ed.learnLineUntil);
                return;
            }
            if (false) {}
            else if (r == NineHandsWindow::idLatch)     pr.setParamValue ("midiFsMode", 0.0f);
            else if (r == NineHandsWindow::idMomentary) pr.setParamValue ("midiFsMode", 1.0f);
            else if (r >= 50 && r <= 52) pr.setParamValue ("sensitivity", (float) (r - 50));
            else if (r >= 100 && r < 200) pr.applyFactoryPreset (r - 100);
            else if (r > 200 && r < 300)  pr.loadUserPreset (r - 200);
            else if (r > 300 && r < 400)  pr.saveUserPreset (r - 300);
            else if (r >= 1000) { ed.handleMidiMenu (r); return; }
            
        });
}
