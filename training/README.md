# Meridian — Canada Sales Training Deck

`Meridian-Canada-Training.pptx` — a 14-slide, presentation-ready deck for training
sales reps on **what Meridian is and what it offers**, for the **Canada** market.

The emphasis is product understanding (not closing scripts): reps should walk out able
to explain the platform clearly. It **leads with the AI phone agent**, then reveals the
full intelligence platform underneath.

Facts are sourced from the actual Meridian repo (`alphasaleaidan/meridian`) — canonical
pricing from `src/billing/fee_terms.py`, the phone-agent behaviour from the Vapi webhook,
the camera design doc, the AI analyzers, and the Canada compliance posture.

## Agenda

| # | Slide | Purpose |
|---|-------|---------|
| 1 | Title | What Meridian is & what it offers (Canada) |
| 2 | What Meridian Is | The big picture: answers the phone, watches the floor, reads the register |
| 3 | Three Systems, One Dashboard | How phone + cameras + POS combine |
| 4 | The AI Phone Agent | What it does — the lead capability |
| 5 | Every Missed Call Is Missed Revenue | Why the phone agent matters |
| 6 | Camera Intelligence | What Vision tracks + zero hardware + privacy |
| 7 | The AI Analytics Engine | Money-Left score + the analysis engines |
| 8 | Fusion Intelligence | Combined-source insight (the moat) |
| 9 | One Dashboard, on Their Phone | What the owner actually sees |
| 10 | How It Connects | POS / cameras / phone setup, read-only |
| 11 | Who It's For | Canadian verticals |
| 12 | Built for Canada | PIPEDA, Quebec Law 25, CASL, CAD, bilingual |
| 13 | Plans & Pricing (Canada) | Standard / Premium / Command tiers |
| 14 | What Meridian Is (recap) | One-breath summary |

## Key facts baked in (current as of the repo)

- **Pricing (CAD, canonical):** Standard **CA$350** · Premium **CA$500** · Command **CA$700** /mo.
  Every tier includes the full analytics engine + camera intelligence; the **AI phone agent**
  is the axis (Premium+). Per-order Meridian fee: CA$0 / CA$1.99 / CA$1.39. Calls: 3 min
  included, then CA$0.45/min, capped at 5 min.
- **Phone agent:** answers in <2s, 24/7, takes orders conversationally → POS, texts a
  pay-by-text link, books appointments, bilingual EN/FR (fr-CA voice).
- **Cameras:** connect existing cameras (no hardware shipped); counts only, no video stored,
  designed outside Quebec Law 25 biometric scope.
- **POS:** Square (live), Clover (live), Toast (approved partner, scheduled onboarding),
  others via CSV. One-click, read-only OAuth.

Every slide includes speaker notes.

## Note on rendering

Built with `pptxgenjs`; passes the pptx structural validator and content QA. Visual preview
images could not be generated in the build environment (LibreOffice headless plugin missing),
so open in PowerPoint/Keynote to eyeball layout before presenting.
