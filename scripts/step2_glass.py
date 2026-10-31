with open('frontend/src/index.css', 'r', encoding='utf-8') as f:
    c = f.read()

old_glass = '''/* Glass Spec: Light (0.72 white, 14px blur) / Dark (0.62 carbon #18181B, 14px blur) */
.glass-surface {
  background: rgba(255, 255, 255, 0.72) !important;
  border-color: rgba(255, 255, 255, 0.85) !important;
  box-shadow: 0 1px 2px rgba(11, 27, 51, 0.06), 0 8px 24px -12px rgba(11, 27, 51, 0.18) !important;
  -webkit-backdrop-filter: blur(14px) saturate(140%) !important;
  backdrop-filter: blur(14px) saturate(140%) !important;
}

html.dark .glass-surface,
.dark .glass-surface {
  background: rgba(24, 24, 27, 0.62) !important;
  border-color: rgba(255, 255, 255, 0.08) !important;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 8px 24px -12px rgba(0, 0, 0, 0.6) !important;
  -webkit-backdrop-filter: blur(14px) saturate(130%) !important;
  backdrop-filter: blur(14px) saturate(130%) !important;
}

@supports not (backdrop-filter: blur(1px)) {
  .glass-surface {
    background: var(--surface) !important;
  }
}'''

new_glass = '''/* ==========================================================================
   STEP 2: GLASSMORPHISM (Visible Glass Spec with High Dynamic Depth)
   ========================================================================== */
.glass-surface {
  background: rgba(255, 255, 255, 0.55) !important;
  border: 1px solid rgba(255, 255, 255, 0.9) !important;
  outline: 1px solid rgba(11, 27, 51, 0.08);
  outline-offset: -1px;
  -webkit-backdrop-filter: blur(18px) saturate(170%) !important;
  backdrop-filter: blur(18px) saturate(170%) !important;
  box-shadow: 
    0 1px 2px rgba(11, 27, 51, 0.06), 
    0 14px 36px -16px rgba(11, 27, 51, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.65) !important;
}

html.dark .glass-surface,
.dark .glass-surface,
[data-theme="dark"] .glass-surface {
  background: rgba(28, 28, 32, 0.50) !important;
  border: 1px solid rgba(255, 255, 255, 0.12) !important;
  outline: none;
  -webkit-backdrop-filter: blur(18px) saturate(150%) !important;
  backdrop-filter: blur(18px) saturate(150%) !important;
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.10), 
    0 14px 36px -16px rgba(0, 0, 0, 0.7) !important;
}

@supports not (backdrop-filter: blur(1px)) {
  .glass-surface {
    background: rgba(255, 255, 255, 0.96) !important;
  }
  html.dark .glass-surface,
  .dark .glass-surface,
  [data-theme="dark"] .glass-surface {
    background: rgba(24, 24, 27, 0.96) !important;
  }
}

/* Header bottom hairline */
#app-header-bar::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, rgba(47, 91, 232, 0.55) 0%, rgba(47, 91, 232, 0.15) 50%, transparent 100%);
  pointer-events: none;
}'''

assert old_glass in c, "old_glass not found"
c = c.replace(old_glass, new_glass)

with open('frontend/src/index.css', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

# Update Dashboard.jsx to ensure hero banner has glass-surface
with open('frontend/src/pages/Dashboard.jsx', 'r', encoding='utf-8') as f:
    dash = f.read()

target_hero = '<div className="relative rounded-lg p-6 sm:p-7 overflow-hidden bg-surface border border-border shadow-card select-none text-text">'
repl_hero = '<div className="hero-glass-card relative rounded-2xl p-6 sm:p-7 overflow-hidden glass-surface border border-border shadow-card select-none text-text">'

if target_hero in dash:
    dash = dash.replace(target_hero, repl_hero)
    with open('frontend/src/pages/Dashboard.jsx', 'w', encoding='utf-8', newline='') as f:
        f.write(dash)
    print('Updated Dashboard hero card to glass-surface')

print('Step 2 applied successfully.')
