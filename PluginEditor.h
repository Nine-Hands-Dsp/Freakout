#pragma once

#include "PluginProcessor.h"
#include <juce_gui_basics/juce_gui_basics.h>
#include "Layout.h"
#include "NineHandsMenu.h"

//==============================================================================
// Potard concentrique RANGE : chapeau central = GAIN, jupe moletee = ONSET.
// Les potards (photo du kit, reflets fixes) font partie du fond : seuls les reperes creme peints tournent.
//==============================================================================
class ConcentricKnob : public juce::Component
{
public:
    ConcentricKnob (juce::RangedAudioParameter& gain, juce::RangedAudioParameter& onset);
    void paint (juce::Graphics&) override {}
    bool hitTest (int x, int y) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    void mouseDoubleClick (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;
    int dragging = -1;                        // 0 = gain, 1 = onset
    int rightZone = 0;                        // zone du dernier clic droit (0 = gain, 1 = onset) : MIDI Learn
    std::function<void()> onRightClick, onUserChange, onValue;
    std::function<void (int)> onTouched;      // ligne d'etat
    float valueOf (int i) const { return i == 0 ? gainV : onsetV; }

private:
    int zoneAt (juce::Point<float> p) const;
    void setV (int which, float v);
    juce::ParameterAttachment gainAtt, onsetAtt;
    float gainV = 5.0f, onsetV = 5.0f, startV = 0.0f;
};

//==============================================================================
// Selecteur TYPE a 7 positions (crans de 45 degres), rotation animee
//==============================================================================
class TypeKnob : public juce::Component
{
public:
    explicit TypeKnob (juce::RangedAudioParameter& p);
    void paint (juce::Graphics&) override {}
    bool hitTest (int x, int y) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseDrag (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;
    bool tick();                               // animation (timer de l'editeur)
    float getShownAngle() const { return shownAngle; }
    std::function<void()> onRightClick, onUserChange;

private:
    void moveTo (int p);
    juce::ParameterAttachment attachment;
    int pos = 3, dragStartPos = 3;
    float shownAngle = 0.0f, targetAngle = 0.0f;
};

//==============================================================================
// Inverseur a levier (photos du kit NINE HANDS | DSP : haut = ON, milieu, bas = OFF)
//==============================================================================
class LeverSwitch : public juce::Component
{
public:
    explicit LeverSwitch (juce::RangedAudioParameter& p);
    void paint (juce::Graphics&) override;
    bool hitTest (int x, int y) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseWheelMove (const juce::MouseEvent&, const juce::MouseWheelDetails&) override;
    void tick (double nowMs);
    juce::Image strip;
    std::function<void()> onRightClick, onUserChange;

private:
    juce::ParameterAttachment attachment;
    bool on = false;
    int shownFrame = 0, targetFrame = 0;
    double transitionUntil = 0.0;
};

//==============================================================================
// Footswitch (reference Echoflex) : bascule a l'appui ; MOMENTARY ON = actif tant qu'on appuie.
// Tant qu'on appuie : bouton enfonce dans son ecrou (fs_down.png) + disque assombri.
//==============================================================================
class FootSwitchArea : public juce::Component
{
public:
    FootSwitchArea (juce::RangedAudioParameter& active, std::atomic<float>* momentary);
    void paint (juce::Graphics&) override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseUp (const juce::MouseEvent&) override;
    bool hitTest (int x, int y) override;
    std::function<void()> onRightClick, onUserChange;
    juce::Image down;

private:
    bool value = false, pressed = false;
    std::atomic<float>* mom = nullptr;
    juce::ParameterAttachment attachment;
};

//==============================================================================
// menus au design d'Octopus + poignee de redimensionnement discrete
struct FreakoutLookAndFeel : public NineHandsMenu::MenuLnf
{
    void drawCornerResizer (juce::Graphics& g, int w, int h, bool over, bool dragging) override
    {
        const float a = dragging ? 0.55f : (over ? 0.38f : 0.16f);
        g.setColour (juce::Colours::white.withAlpha (a));
        const float s = (float) juce::jmin (w, h);
        for (float k : { 0.30f, 0.58f, 0.86f })
            g.drawLine (s * (1.0f - k), s - 1.0f, s - 1.0f, s * (1.0f - k), 1.0f);
    }
};

//==============================================================================
class FreakoutAudioProcessorEditor : public juce::AudioProcessorEditor,
                                     private juce::Timer
{
public:
    explicit FreakoutAudioProcessorEditor (FreakoutAudioProcessor&);
    ~FreakoutAudioProcessorEditor() override;

    void paint (juce::Graphics&) override;
    void resized() override;
    void parentHierarchyChanged() override;
    void mouseDown (const juce::MouseEvent&) override;
    void mouseMove (const juce::MouseEvent&) override;
    void mouseExit (const juce::MouseEvent&) override;

    // Repere du fond (pedale plein cadre, image 1235 x 1800 px / 2). Hauteurs de fenetre des pedales simples :
    // taille par defaut = taille minimale 493 px (« 60 % »), 75 % = 719, 100 % = 958 px, jusqu'a 150 %.
    static constexpr float baseW = layout::frameW;
    static constexpr float baseH = layout::frameH;
    static constexpr int defaultH = 493;
    static constexpr int refH = 958;
    static constexpr int maxH = refH * 3 / 2;

    void setScaledHeight (int h);
    void forceRenderScale (float sc) { forcedScale = sc; rebuildCaches (sc); }   // captures (outil de rendu)
    void pressFootswitchForCapture (bool down);                                    // captures (outil de rendu)
    static constexpr int numSizes = 3;          // 60 % (defaut d'origine) / 75 % / 100 %
    static int sizeHeight (int idx);
    void showStatus();

private:
    void timerCallback() override;
    void useSoftwareRenderer();
    void visibilityChanged() override;
    void askRepaint (juce::Rectangle<int> r);
    void showContextMenu (int learnIdx = -1);     // learnIdx >= 0 : clic droit sur une commande (MIDI Learn en tete du menu)
    void addMidiMenu (juce::PopupMenu& menu, int learnIdx);
    void handleMidiMenu (int r);
    void showPresetMenu();
    void stepPreset (int delta);
    void rebuildCaches (float scale = 0.0f);
    float physicalScale() const;
    juce::Rectangle<int> scaled (juce::Rectangle<float> r) const;
    juce::String buildStatusLine() const;
    juce::String buildInfoLine() const;
    juce::String buildPresetLine() const;
    void buildPrint();
    void drawPrint (juce::Graphics&);
    void drawLeds (juce::Graphics&);
    void drawKnobs (juce::Graphics&);
    void drawDisplay (juce::Graphics&);

    FreakoutAudioProcessor& proc;
    FreakoutLookAndFeel lnf;

    juce::Image background, bgScaled, glowStrip, glowScaled[5], ledOn, ledOnS;
    int cacheW = 0, cacheH = 0;
    float cacheScale = 0.0f, forcedScale = 0.0f;
    int resizeSettle = 0;
    void* lastPeer = nullptr;
    double lastPaintMs = 0.0, repaintAskedMs = 0.0, lastScaleCheckMs = 0.0, lastRendererCheckMs = 0.0;
    juce::Typeface::Ptr regFace, labelFace, boldFace, lightFace;
    juce::Path printDark, printLight, framePath, wavePath;   // serigraphie vectorielle (unites du plugin)
    std::unique_ptr<juce::Drawable> logo;

    ConcentricKnob range;
    TypeKnob typeKnob;
    LeverSwitch momentarySw, drySw;
    FootSwitchArea foot;

    // animation
    float ledLevel = 0.0f, meterShown = 0.0f;
    float ledB[9] {}, drawnLedB[9] {};
    float drawnGlow = -1.0f;
    int lastChanged = -1;
    float statusAlpha = 0.0f, drawnStatus = -1.0f;
    double statusUntil = 0.0;
    juce::String lastLine1, lastInfo, lastPreset;
    float lastValues[8];
    int lastPresetCounter = 0, lastMidiCount = 0, midiFlash = 0;
    int hoverZone = 0, drawnHover = -1;

    // MIDI Learn : message dans l'afficheur (attente, puis « <Commande> = CC n » 2 s)
    juce::String learnLine;
    double learnLineUntil = 0.0;

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (FreakoutAudioProcessorEditor)
};
