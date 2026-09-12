# Design System: VyaparSathi

## 1. Visual Theme & Atmosphere

VyaparSathi is a modern civic-finance utility for rural MSME entrepreneurs: clear enough for a first-time digital user and rigorous enough for a serious financial decision. It should feel like a national digital service — structured, trustworthy, data-led, and easy to use in daylight on a budget phone.

Density is **Daily App Balanced (5/10)**. Variance is **Structured Offset (5/10)**: use a strong left-aligned hierarchy with occasional offset evidence panels, never symmetrical card grids for their own sake. Motion is **Fluid CSS (4/10)**: short, weighty transitions that communicate progress and status without distracting from reading.

## 2. Color Palette & Roles

- **Civic Canvas** (#FAF8FF) — page background; calm, bright and legible in daylight.
- **Pure Surface** (#FFFFFF) — form panels, report sections, and elevated content.
- **Civic Ink** (#131B2E) — primary text; never use pure black.
- **Muted Slate** (#5A6270) — helper text, labels, and limitations.
- **Structural Line** (#CBD5E1) — 1px dividers and form borders.
- **Sovereign Navy** (#002546) — primary actions, active steps, financial structures and authority panels.
- **Saffron Action** (#E65100) — selected business states, action cues and information hierarchy.
- **Trust Green** (#1B8755) — positive verified evidence, completed steps and scheme-positive signals only.
- **Red Signal** (#BA1A1A) — errors and verification-required warnings only.

The thin national tricolour header rule is the only permitted gradient. No neon colors, outer glows, or decorative gradients. Keep contrast high enough for users aged 30–50 reading on small or older screens.

## 3. Typography Rules

- **Display and headings:** `Plus Jakarta Sans`, `Avenir Next`, `Noto Sans`, sans-serif; compact but not cramped, using weight and spacing for hierarchy.
- **Body:** `Plus Jakarta Sans`, `Avenir Next`, `Noto Sans`, sans-serif; 16px minimum for primary explanatory copy, relaxed 1.55 line-height, and 68ch maximum line length.
- **Language:** English only until a complete translated experience is ready.
- **Numbers and dense metadata:** `ui-monospace`, `SFMono-Regular`, monospace only where tabular alignment helps.
- Avoid serif type in dashboards, forms, and reports. Never use Inter, Times New Roman, Georgia, or decorative display faces.
- Scale headings with `clamp()`, keep primary reading text at or above 14px, and never rely on color alone to communicate status.

## 4. Component Stylings

- **Buttons:** 44px minimum touch target, flat Sovereign Navy primary, white/outlined secondary, clear disabled state, and a small tactile translate on press. No glow.
- **Cards and panels:** use disciplined 3–6px radii, thin structural borders, and only an ultra-subtle shadow where elevation explains hierarchy. Dense data should use dividers and whitespace rather than nested cards.
- **Inputs:** label above the field, strong focus ring in Sovereign Navy with a Saffron visible keyboard outline, helper text, and errors below the field. Never use floating labels.
- **Evidence badges:** compact uppercase labels with explicit meanings: PUBLIC DATA, CALCULATED, USER INPUT, VERIFICATION REQUIRED, VERIFIED GOVT RULE.
- **Visual data:** prefer horizontal bars, compact metric strips, radius bands, scenario tiles, and a single emphasized number. Always pair a visual with its text label and source scope.
- **Loading:** use skeleton-like blocks and short status copy; circular motion is reserved for small inline progress indicators.
- **Empty and error states:** explain what is missing, why it matters, and the next safe action.

## 5. Layout Principles

Use a centered max-width of 1240px with 16–24px gutters. Build on CSS Grid, with a single-column collapse below 768px. The first screen uses an asymmetric 1.4fr/0.8fr split: action copy on the left, service proof on the right. Assessment screens keep the task content dominant and use a five-stage progress map above it.

Prefer one strong primary action per viewport. Use 2-column evidence layouts and visual strips instead of three equal feature cards. Keep every element in its own spatial zone; no text over images, no overlapping panels, and no horizontal overflow on mobile.

## 6. Motion & Interaction

Use 160–220ms ease-out transitions and a spring-like tactile press (`transform: translateY(1px)`) for buttons. Stagger only the entrance of major data groups; animate opacity and transform, never layout properties. Respect `prefers-reduced-motion`. Active evidence bars may use a very subtle shimmer once on load, but never loop distracting motion.

## 7. Responsive Rules

- Below 768px, collapse all grids to one column and make actions full width.
- Keep touch targets at least 44px high.
- Keep primary body text at 16px and allow headings to scale down with `clamp()`.
- Turn the journey map into a compact scrollable step rail with the current step always legible.
- Stack report metric strips, finance panels, and visual evidence bands without horizontal scrolling.

## 8. Anti-Patterns (Banned)

- No emojis in the product UI.
- No Inter or generic serif fonts.
- No pure black, neon, purple/blue glow, decorative gradients beyond the thin tricolour header rule, or fake 3D effects.
- No centered hero with filler copy, scroll arrows, or “next-gen” language.
- No equal three-column card rows used as decoration.
- No unexplained scores, fake precision, or round-number promises.
- No overlapping content, tiny body copy, low-contrast labels, or color-only status indicators.
- No invented competition, demand, eligibility, or price data; every visual must retain its source scope and limitations.
