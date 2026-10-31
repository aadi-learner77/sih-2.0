with open('frontend/src/index.css', 'r', encoding='utf-8') as f:
    c = f.read()

# Update light mode base
c = c.replace('--bg: #F3F5F9;', '--bg: #F1F4FA;')

# Update ambient background layer
old_ambient = '''/* Ambient Background Layer: One fixed, static, very soft layer */
.ambient-background {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-color: var(--bg);
  background-image: 
    radial-gradient(circle at 0% 0%, rgba(31, 75, 255, 0.07) 0%, transparent 45%),
    radial-gradient(circle at 100% 100%, rgba(255, 153, 51, 0.06) 0%, transparent 45%);
}

html.dark .ambient-background,
.dark .ambient-background {
  background-color: var(--bg);
  background-image: 
    radial-gradient(circle at 0% 0%, rgba(150, 160, 190, 0.07) 0%, transparent 45%),
    radial-gradient(circle at 100% 100%, rgba(59, 108, 255, 0.06) 0%, transparent 45%);
}'''

new_ambient = '''/* ==========================================================================
   STEP 1: AMBIENT COLOUR FIELD (Visible, static, 4 large colour fields)
   ========================================================================== */
.ambient-background {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-color: #F1F4FA;
  background-image: 
    radial-gradient(circle at 1px 1px, rgba(11, 27, 51, 0.05) 1px, transparent 0),
    radial-gradient(circle 60vw at 0% 0%, rgba(31, 75, 255, 0.26) 0%, transparent 70%),
    radial-gradient(circle 50vw at 100% 100%, rgba(255, 153, 51, 0.20) 0%, transparent 65%),
    radial-gradient(circle 45vw at 0% 100%, rgba(34, 211, 238, 0.14) 0%, transparent 65%),
    radial-gradient(circle 45vw at 100% 0%, rgba(139, 92, 246, 0.12) 0%, transparent 65%);
  background-size: 24px 24px, 100% 100%, 100% 100%, 100% 100%, 100% 100%;
}

html.dark .ambient-background,
.dark .ambient-background,
[data-theme="dark"] .ambient-background {
  background-color: #0A0A0B;
  background-image: 
    radial-gradient(circle at 1px 1px, rgba(255, 255, 255, 0.05) 1px, transparent 0),
    radial-gradient(circle 60vw at 0% 0%, rgba(59, 108, 255, 0.28) 0%, transparent 70%),
    radial-gradient(circle 45vw at 100% 0%, rgba(190, 195, 220, 0.10) 0%, transparent 65%),
    radial-gradient(circle 45vw at 0% 100%, rgba(79, 70, 229, 0.16) 0%, transparent 65%),
    radial-gradient(circle 50vw at 100% 100%, rgba(255, 153, 51, 0.10) 0%, transparent 65%);
  background-size: 24px 24px, 100% 100%, 100% 100%, 100% 100%, 100% 100%;
}'''

assert old_ambient in c, "old_ambient not found"
c = c.replace(old_ambient, new_ambient)

with open('frontend/src/index.css', 'w', encoding='utf-8', newline='') as f:
    f.write(c)

print('Step 1 applied successfully to index.css')
