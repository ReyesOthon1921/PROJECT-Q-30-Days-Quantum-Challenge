# AgroQ Phase 3.3.1 — Notification Control UI Refinement

## Problems corrected

- Tiny checkboxes separated from their labels
- Labels visually drifting to the right
- Unclear on/off state
- Unavailable channels appearing selectable
- Weak focus indication
- Small mobile touch targets
- No explanation of what each channel does
- No clear save-state confirmation

## New interaction model

- Native HTML checkbox inputs preserve keyboard and screen-reader behavior.
- Delivery channels are displayed as switch cards with visible On/Off text.
- Full cards provide larger click and touch targets.
- Disabled channels display Setup required and explain the missing configuration.
- Event preferences use larger checkbox cards rather than isolated tiny boxes.
- Fieldset and legend elements identify logical groups.
- Focus-visible outlines make keyboard navigation obvious.
- Mobile layouts stack controls without separating labels from inputs.
