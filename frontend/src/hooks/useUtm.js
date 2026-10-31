import { useState, useEffect } from 'react';

/**
 * useUtm - Hook to capture and persist UTM query parameters on initial page load.
 * Stores captured parameters in sessionStorage and exposes them.
 * Does NOT attach to API calls or alter network requests.
 */
export function useUtm() {
  const [utmParams, setUtmParams] = useState(() => {
    try {
      const stored = sessionStorage.getItem('pramaan_utm_params');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    try {
      const searchParams = new URLSearchParams(window.location.search);
      const captured = {};
      let hasUtm = false;

      searchParams.forEach((val, key) => {
        if (key.toLowerCase().startsWith('utm_') || key.toLowerCase() === 'ref') {
          captured[key] = val;
          hasUtm = true;
        }
      });

      if (hasUtm) {
        const merged = { ...utmParams, ...captured };
        sessionStorage.setItem('pramaan_utm_params', JSON.stringify(merged));
        setUtmParams(merged);
      }
    } catch (e) {
      console.warn('Could not parse UTM query parameters:', e);
    }
  }, []);

  return utmParams;
}
