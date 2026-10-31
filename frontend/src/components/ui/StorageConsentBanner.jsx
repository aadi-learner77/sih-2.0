import React, { useState } from 'react';
import { ShieldCheck, X } from 'lucide-react';

/**
 * StorageConsentBanner - Non-blocking notice explaining the use of local storage
 * exclusively for session authentication and interface theme preferences.
 */
export default function StorageConsentBanner() {
  const [visible, setVisible] = useState(() => {
    try {
      return typeof window !== 'undefined' && !localStorage.getItem('pramaan_storage_consent');
    } catch {
      return false;
    }
  });

  const handleAcknowledge = () => {
    try {
      localStorage.setItem('pramaan_storage_consent', 'true');
    } catch (_e) {}
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <aside 
      id="storage-consent-banner"
      role="region"
      aria-label="Storage and privacy notice"
      className="fixed bottom-3 left-4 right-4 sm:left-6 sm:right-auto sm:max-w-md z-40 p-3.5 bg-surface rounded-xl border border-border shadow-xl glass-surface text-xs text-text transition-all duration-300 animate-fadeIn"
    >
      <div className="flex items-start gap-2.5">
        <div className="p-1.5 rounded-lg bg-primary/10 text-primary shrink-0 mt-0.5">
          <ShieldCheck className="w-4 h-4" />
        </div>
        <div className="flex-1 space-y-1">
          <div className="font-semibold text-text text-xs flex items-center justify-between">
            <span>Local Storage & Session Notice</span>
            <button
              type="button"
              onClick={handleAcknowledge}
              className="text-text-muted hover:text-text p-0.5 rounded cursor-pointer"
              aria-label="Dismiss notice"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
          <p className="text-text-muted text-[11px] leading-relaxed">
            PRAMAAN-X uses local browser storage strictly for session authentication (JWT) and theme preferences. No tracking cookies or third-party telemetry scripts are employed.
          </p>
          <div className="pt-1 flex justify-end">
            <button
              type="button"
              onClick={handleAcknowledge}
              className="px-3 py-1 bg-primary text-white text-[11px] font-semibold rounded-lg hover:bg-primary-hover transition-colors cursor-pointer"
            >
              Acknowledge
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
}
