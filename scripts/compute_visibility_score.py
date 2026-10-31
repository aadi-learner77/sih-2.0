import os
import glob
from PIL import Image
import numpy as np

SCREENSHOTS_DIR = 'audit_screenshots'
PAIRS = [
  ('v2_before_dashboard_light.png', 'v2_after_dashboard_light.png', 'Dashboard Light'),
  ('v2_before_dashboard_dark.png', 'v2_after_dashboard_dark.png', 'Dashboard Dark'),
  ('v2_before_evidence-lens_light.png', 'v2_after_evidence-lens_light.png', 'Evidence Lens Light'),
  ('v2_before_evidence-lens_dark.png', 'v2_after_evidence-lens_dark.png', 'Evidence Lens Dark'),
  ('v2_before_manual-review-queue_light.png', 'v2_after_manual-review-queue_light.png', 'Review Queue Light'),
  ('v2_before_manual-review-queue_dark.png', 'v2_after_manual-review-queue_dark.png', 'Review Queue Dark'),
  ('v2_before_document-intelligence_light.png', 'v2_after_document-intelligence_light.png', 'Doc Intel Light'),
  ('v2_before_document-intelligence_dark.png', 'v2_after_document-intelligence_dark.png', 'Doc Intel Dark'),
  ('v2_before_audit-ledger_light.png', 'v2_after_audit-ledger_light.png', 'Audit Ledger Light'),
  ('v2_before_audit-ledger_dark.png', 'v2_after_audit-ledger_dark.png', 'Audit Ledger Dark'),
  ('v2_before_regulations_light.png', 'v2_after_regulations_light.png', 'Regulations Light'),
  ('v2_before_regulations_dark.png', 'v2_after_regulations_dark.png', 'Regulations Dark'),
]

print("=" * 60)
print("VISIBILITY SCORE: BEFORE vs AFTER MORPHISM PIXEL DELTAS")
print("=" * 60)

results = []

for before_name, after_name, label in PAIRS:
    p_before = os.path.join(SCREENSHOTS_DIR, before_name)
    p_after = os.path.join(SCREENSHOTS_DIR, after_name)

    if not os.path.exists(p_before) or not os.path.exists(p_after):
        print(f"Skipping {label}: missing file(s)")
        continue

    img_b = Image.open(p_before).convert('RGB')
    img_a = Image.open(p_after).convert('RGB')

    arr_b = np.array(img_b, dtype=np.float32)
    arr_a = np.array(img_a, dtype=np.float32)

    # Ensure same shape
    h = min(arr_b.shape[0], arr_a.shape[0])
    w = min(arr_b.shape[1], arr_a.shape[1])
    arr_b = arr_b[:h, :w]
    arr_a = arr_a[:h, :w]

    # Full page delta
    diff = np.abs(arr_a - arr_b) / 255.0
    full_delta = np.mean(diff) * 100

    # Header region (y: 0-70, x: 0-w)
    header_diff = diff[0:min(70, h), 0:w]
    header_delta = np.mean(header_diff) * 100 if header_diff.size > 0 else 0

    # Sidebar region (y: 64-h, x: 0-260)
    sidebar_diff = diff[64:h, 0:min(260, w)]
    sidebar_delta = np.mean(sidebar_diff) * 100 if sidebar_diff.size > 0 else 0

    # KPI / Content region (y: 120-450, x: 260-w)
    kpi_diff = diff[min(120, h):min(450, h), min(260, w):w]
    kpi_delta = np.mean(kpi_diff) * 100 if kpi_diff.size > 0 else 0

    # Combined Header + Sidebar + KPI region mask
    mask = np.zeros((h, w), dtype=bool)
    mask[0:min(70, h), :] = True
    mask[64:h, 0:min(260, w)] = True
    mask[min(120, h):min(450, h), min(260, w):w] = True
    
    combined_delta = np.mean(diff[mask]) * 100

    results.append({
        'label': label,
        'full': full_delta,
        'header': header_delta,
        'sidebar': sidebar_delta,
        'kpi': kpi_delta,
        'combined': combined_delta
    })

    status = "PASS (>= 3%)" if combined_delta >= 3.0 else "FAINT (< 3%)"
    print(f"{label:22} | Combined: {combined_delta:5.2f}% | Header: {header_delta:5.2f}% | Sidebar: {sidebar_delta:5.2f}% | KPI: {kpi_delta:5.2f}% | {status}")

print("=" * 60)
avg_light = np.mean([r['combined'] for r in results if 'Light' in r['label']])
avg_dark = np.mean([r['combined'] for r in results if 'Dark' in r['label']])
print(f"Overall Average Combined Delta (Light Theme): {avg_light:.2f}% (Threshold: >= 3.0%)")
print(f"Overall Average Combined Delta (Dark Theme):  {avg_dark:.2f}% (Threshold: >= 3.0%)")
print("=" * 60)

