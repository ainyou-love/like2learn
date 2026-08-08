Create a single-file static HTML page (no build step, no external JS libraries) that renders my reading notes as a "Vietnamese savings passbook" (sổ tiết kiệm) themed notebook. This is entry No.[XX] in a series — follow this design system EXACTLY so all entries look identical.

CONTENT
- Language: Vietnamese. I will provide the notes below; keep their structure: numbered main sections, each with bullet points and one "lesson/callout" summary.
- [PASTE NOTES HERE]

DESIGN TOKENS (use these exact values as CSS variables)
- --paper:#F3F5EE; --paper-deep:#EAEEE3; --ink:#1C2B22; --ink-soft:#44544A;
  --green:#2F5D4A; --green-line:#C3D0C0; --brass:#9C7A2E; --seal:#B0492F; --card:#FBFCF8; --radius:10px
- Body background: --paper plus a subtle ruled-paper effect:
  repeating-linear-gradient(transparent 0 31px, rgba(47,93,74,.045) 31px 32px)
- Fonts (Google Fonts, must support Vietnamese subset):
  display = "Bricolage Grotesque" (600/700), body = "Be Vietnam Pro" (400/500/600),
  utility/numbers = "IBM Plex Mono" (400/500)

LAYOUT
- Grid: max-width 1240px, two columns — fixed 288px left sidebar + fluid main column, 48px gap.
- Sidebar: sticky (top:0, height:100vh, own scrollbar). Header is a "passbook cover" card:
  double border effect (2px solid --green outside + 1px dashed --green-line inset), small red
  uppercase mono label "Sổ ghi chép · No.[XX]", then the notebook title in the display font.
  Below: an <ol> table of contents — each link shows a right-aligned mono index number in
  --brass plus the section title; active item gets --card background, --green bold text, and a
  3px --seal left border.
- Hero: mono red uppercase kicker, big display-font H1 in --green (clamp 34–56px), a 1–2
  sentence subtitle, and 2–3 pill-shaped mono meta tags. Top-right: a rotated (~7deg) circular
  red rubber-stamp SVG reading "ĐÃ GHI / SỔ · [YEAR]" (two concentric circles, outer solid,
  inner dashed). Hide the stamp under 900px.
- Each section = a "ledger entry" card: --card background, 1px --green-line border, radius 10px,
  scroll-margin-top:24px. Card header: 2-column grid — left has a mono brass eyebrow
  ("Mục 01", "Mục 02"…), the H2 in display font --green, and one italic one-line summary;
  right has the illustration frame. Header separated from body by a dashed bottom border.
- Illustration frame: 168×138px, 2px solid --green border + inner 1px dashed inset, --paper
  background, rotated -1.4deg like a pasted stamp.
- Body bullets: unstyled <ul>, each <li> prefixed with an em-dash "—" in --brass via ::before;
  bold key phrases with <strong> colored --green.
- End most sections with a callout box: 3px solid --seal left border, --paper background,
  small red uppercase mono label (e.g. "Bài học", "Nguyên tắc") above the text.
- Footer: dashed top border, small mono source line.

ILLUSTRATIONS
- One inline SVG spot illustration per main section, hand-drawn line-art style: fill:none,
  stroke-width:3, round linecaps/joins, viewBox="0 0 160 120". Base stroke --green, accents via
  classes .b (--brass) and .s (--seal), .thin for stroke-width:2. Each illustration must be a
  simple visual metaphor for that section's idea (5–12 shapes max). No external images.

BEHAVIOR / TECHNICAL REQUIREMENTS
- Scrollspy: IntersectionObserver with rootMargin '-20% 0px -70% 0px' toggles .active on TOC
  links; on desktop only, auto-scroll the active link into view (block:'nearest').
- Smooth scrolling via CSS scroll-behavior, fully disabled inside a
  @media (prefers-reduced-motion: reduce) block along with all animations/transitions.
- Mobile (max-width:900px): single column; sidebar becomes an off-canvas drawer
  (width min(82vw,320px), height 100vh with 100dvh override for iOS Safari, translateX
  transition) opened by a fixed pill button "☰ MỤC LỤC" bottom-left (--green background).
  Include a semi-transparent backdrop overlay; drawer closes on: backdrop tap, Escape key, or
  TOC link tap. Manage open state in one function that syncs the drawer class, backdrop class,
  and aria-expanded on the button. Section header stacks to one column; illustration goes
  full-width (max 220px).
- Accessibility: aria-label on nav, aria-expanded/aria-controls on the toggle, aria-hidden on
  decorative SVGs, visible keyboard focus.
- Vanilla JS only, everything inline in one .html file. Body text 16px, line-height 1.75.
