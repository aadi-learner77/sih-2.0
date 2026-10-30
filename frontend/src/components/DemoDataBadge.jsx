import React from 'react';
import { AlertTriangle } from 'lucide-react';

/**
 * Reusable Demo Data Badge:
 * Required on any screen when falling back to mock / simulated data because
 * backend is unreachable or returning empty.
 * Styled cleanly with neutral glassmorphism surface and high-contrast text.
 */
export default function DemoDataBadge({ className = '', message = 'Demo data' }) {
  return (
    <div
      className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-surface-2 text-text border border-border shadow-2xs ${className}`}
      title="Backend response unavailable; displaying fallback demonstration dataset"
    >
      <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
